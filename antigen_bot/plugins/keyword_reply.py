"""Auto Reply anything you want to Contact/Room"""
from __future__ import annotations
import argparse
import asyncio
from cgitb import text
from re import S
import sys
import os
from typing import Dict, List, Literal, Optional, Sequence, Union
import json
from logging import Logger
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from wechaty import (
    Contact,
    FileBox,
    MiniProgram,
    Room,
    UrlLink,
    WechatyPlugin,
    MessageType,
    Message
)
from wechaty_puppet import get_logger
from tap import Tap

from antigen_bot.plugins.config import Conversation
from antigen_bot.utils import remove_at_info


TYPE_MAPS: Dict[str, MessageType] = {
    'text': MessageType.MESSAGE_TYPE_TEXT,
    'image': MessageType.MESSAGE_TYPE_IMAGE,
    'mini_program': MessageType.MESSAGE_TYPE_MINI_PROGRAM,
    'url': MessageType.MESSAGE_TYPE_URL
}
TYPE2STR_MAP: Dict[MessageType, str] = {type: name for name, type in TYPE_MAPS.items()}

@dataclass(init=False)
class Reply:
    """Things you reply"""
    def __init__(self, text: Union[str, dict], type: Union[MessageType, str, int] = MessageType.MESSAGE_TYPE_TEXT) -> None:
        self.text = text
        if isinstance(type, str):
            if type not in TYPE_MAPS:
                raise ValueError(f'{type} is not a valid type')
            type = TYPE_MAPS[type]
        elif isinstance(type, int):
            type = MessageType(type)

        if type not in TYPE2STR_MAP:
            raise ValueError(f'{type} is not a valid type')

        self.type = type

    text: Union[str, dict]
    # 1. 如果是纯文本，则直接返回text的文本内容
    # 2. 如果是Image，则直接社基于：FileBox.from_file来加载
    type: Optional[MessageType] = None

    def to_dict(self) -> dict:
        """save reply to dict data"""
        return dict(text=self.text, type=TYPE2STR_MAP[self.type])


@dataclass_json
@dataclass
class Rule:
    """Things you reply"""
    def __init__(self, keyword: str, convs: List[dict] = None, msgs: List[dict] = None) -> None:
        """init the Rule"""
        convs, msgs = convs or [], msgs or []
        self.keyword = keyword
        
        self.convs = [Conversation(**conv) for conv in convs]
        self.msgs = []
        for msg in msgs:
            if isinstance(msg, str):
                self.msgs.append(Reply(msg))
            else:
                self.msgs.append(Reply(**msg))
        
    #TODO: 支持正则
    keyword: str
    convs: List[Conversation] = field(default_factory=list)
    msgs: List[Reply] = field(default_factory=list)

    async def is_target_conv(self, conv: Union[Contact, Room]) -> bool:
        """check that if the contact/room is the target conversation

        Args:
            conv (Union[Contact, Room]): instance of the contact/room

        Returns:
            bool: if match the conversation
        """
        await conv.ready()
        if isinstance(conv, Contact):
            conv_id, conv_name = conv.contact_id, conv.payload.name
        else:
            conv_id, conv_name = conv.room_id, conv.payload.topic
        
        # TODO: if convs is none, it will reply to anyone
        if not self.convs:
            return True

        for conversation in self.convs:
            if conversation.id == conv_id and conversation.name == conv_name:
                return True
        return False


class KeywordAddParser(Tap):
    """keyword add parser"""
    payload: Optional[str] = None       # the payload of different type
    type: Literal['text', 'image', 'mini-program', 'url-link', 'file', 'contact'] = 'text'  # the type of the payload
    

class KeywordRemoveParser(Tap):
    """keyword remove parser"""
    keyword: str    # the keyword you want to remove
    index: int      # the index of the keyword you want to remove

class KeywordListParser(Tap):
    """keyword list parser"""
    keyword: Optional[str] = None   # list all of the messages under the keyword
    index: int = -1                 # show the index-th message to the user


class KeyWordParser(Tap):
    """keyword parser"""
    def __init__(self, *args, underscores_to_dashes: bool = False, explicit_bool: bool = False, config_files: Optional[List[str]] = None, **kwargs):
        super().__init__(*args, underscores_to_dashes=underscores_to_dashes, explicit_bool=explicit_bool, config_files=config_files, **kwargs)
        self.command_type = ''
        self.parser_type = KeyWordParser()

    def configure(self) -> None:
        self.add_subparser('add', KeywordAddParser, help='add keyword')
        self.add_subparser('remove', KeywordRemoveParser, help='remove keyword')
        self.add_subparser('list', KeywordListParser, help='list keyword')

    # pylint: disable=arguments-differ
    def parse_args(self, args: Optional[Sequence[str]] = None, known_only: bool = False, legacy_config_parsing=False) -> KeyWordParser:
        """parse"""
        args = args or sys.argv
        if 'add' in args:
            self.command_type = 'add'
            self.parser_type = KeywordAddParser()
        elif 'remove' in args:
            self.command_type = 'remove'
            self.parser_type = KeywordRemoveParser()
        elif 'list' in args:
            self.command_type = 'list'
            self.parser_type = KeywordListParser()
        
        if args[-1] == '--help':
            return self
        
        return super().parse_args(args=args, known_only=known_only, legacy_config_parsing=legacy_config_parsing)


class KeyWordReplyPlugin(WechatyPlugin):
    """Reply things base on the config file"""
    def __init__(
        self,
        config_file: Optional[str] = None,
        command_prefixs: Union[str, List[str]] = '$kwr'
    ):
        super().__init__(None)
        if isinstance(command_prefixs, str):
            command_prefixs = [command_prefixs]

        self.command_prefixs = command_prefixs
        self.log: Logger = get_logger(self.name, f'.wechaty/{self.name}.log')

        self.cache_dir = os.path.join('.wechaty', self.name)

        # check the config file
        if not config_file:
            config_file = os.path.join(self.cache_dir, 'config.json')
            if not os.path.exists(config_file):
                raise ValueError(f'the config_file argument is None and there is no default config file<config.json> under cache dir: {self.cache_dir}')
        self.config_file = config_file

    async def match_command(self, text: str) -> Optional[List[str]]:
        """check if the text is a command,

        Args:
            text (str): the text from the message which may be the command

        Returns:
            Optional[List[str]]: the command arguments
        """
        for command_prefix in self.command_prefixs:
            if text.startswith(command_prefix):
                text = text[len(command_prefix) + 1:]
                return text.split()
        return None

    async def _load_rules(self) -> List[Rule]:
        """load the rules from the config file"""
        if not os.path.exists(self.config_file):
            return []

        with open(self.config_file, 'r', encoding='utf-8') as file_handler:
            data = json.load(file_handler)

        return [Rule(**rule) for rule in data]
    
    async def load_reply(self, reply: Reply) -> Union[str, FileBox, MiniProgram, UrlLink]:
        """load the reply from the config file

        Args:
            reply (Reply): the reply you want to load

        Returns:
            _type_: which may be str, Filebox, MiniProgram, UrlLink
        """
        if reply.type == MessageType.MESSAGE_TYPE_TEXT:
            return reply.text
        if reply.type in [MessageType.MESSAGE_TYPE_ATTACHMENT, MessageType.MESSAGE_TYPE_IMAGE, MessageType.MESSAGE_TYPE_VIDEO, MessageType.MESSAGE_TYPE_ATTACHMENT]:
            return FileBox.from_file(reply.text)
        if reply.type == MessageType.MESSAGE_TYPE_MINI_PROGRAM:
            payload = reply.text
            if isinstance(payload, str):
                payload = json.loads(payload)
            return MiniProgram.create_from_json(payload)
        if reply.type == MessageType.MESSAGE_TYPE_URL:
            return UrlLink.create(reply.text, title=None, thumbnail_url=None, description=None)
        
        raise ValueError(f'unknown reply type: {reply.type}')
    
    async def handle_list_command(self, msg: Message, args: KeywordListParser):
        """handle the list command

        Args:
            msg (Message): the message object
            args (KeywordListParser): the argument parser
        """
        # 1. get all of configs

        rules = await self._load_rules()

        # 2. send all of keyword infos
        if not args.keyword:
            info = [
                f'Keywords<{len(rules)}>'
            ]
            for rule in rules:
                info.append(f'{rule.keyword}: messages<{len(rule.msgs)}>')

            await msg.say('\n'.join(info))
            return
        
        # 3. filter the with keyword
        rules = [rule for rule in rules if rule.keyword == args.keyword]
        if not rules:
            info = [
                f'keyword<{args.keyword}> not found',
                'which shoule be one of the following keywords:',
                ','.join([rule.keyword for rule in rules])
            ]
            await msg.say('\n'.join(info))
            return

        if len(rules) > 1:
            await msg.say(f'there are {len(rules)} rules with the keyword<{args.keyword}>, which is not supported now')
            return

        rule = rules[0]
        # 4. send the messages to the users
        if args.index == -1:
            await msg.say(f'keyword<{rule.keyword}> messages<{len(rule.msgs)}>')
            for index, reply in enumerate(rule.msgs):
                await msg.say(f'the {index + 1}-th message: {msg}')
                await asyncio.sleep(1)
                reply = await self.load_reply(reply)
                await msg.say(reply)
                await asyncio.sleep(1)
            return

        await msg.say(f'the {args.index + 1}-th message: {msg}')
        await asyncio.sleep(1)
        reply = await self.load_reply(rule.msgs[args.index])
        await msg.say(reply)
        await asyncio.sleep(1)

    async def handle_add_command(self, msg: Message, args: KeywordAddParser):
        pass

    async def handle_remove_command(self, msg: Message, args: KeywordRemoveParser):
        pass

    async def handle_command_message(self, msg: Message, args: List[str]):
        """handle_command_message is the main function of the plugin

        Args:
            msg (Message): the message object
            args (List[str]): the arguments of commands
        """
        parser = KeyWordParser()
        try:
            parser = parser.parse_args(args=args, known_only=True)
            if parser.command_type == 'help':
                raise argparse.ArgumentError(parser, 'help')
        except argparse.ArgumentError:
            help_info = parser.format_help()
            await msg.say(help_info)
            return
        
        # 1. handle the list command
        if parser.command_type == 'list':
            await self.handle_list_command(msg, parser)
        elif parser.command_type == 'add':
            await self.handle_add_command(msg, parser)
        elif parser.command_type == 'remove':
            await self.handle_remove_command(msg, parser)
    
    async def on_message(self, msg: Message) -> None:
        talker: Contact = msg.talker()
        room: Optional[Room] = msg.room()

        # 1. 判断是否是自己发送的消息
        if msg.is_self():
            return

        # 2. 如果是群聊，可是并没有艾特机器人
        if room and not await msg.mention_self():
            return
        
        # 3. 查找匹配上的Rule
        text = remove_at_info(msg.text())
        args = await self.match_command(text)
        if args:
            await self.handle_command_message(msg, args=args)
            return

        rules = await self._load_rules()
        target_rule: Optional[Rule] = None
        for rule in rules:
            if rule.keyword == text:
                target_rule = rule
                break

        if not target_rule:
            return
        
        # 4. 查找目标对象
        conv = room if room else talker
        is_target_conv = await target_rule.is_target_conv(conv)
        if not is_target_conv:
            return

        # 5. 发送配置好的消息内容
        for message in target_rule.msgs:
            try:
                if message.type == MessageType.MESSAGE_TYPE_TEXT:
                    await msg.say(message.text)
                elif message.type == MessageType.MESSAGE_TYPE_IMAGE:
                    if os.path.exists(message.text):
                        file_box = FileBox.from_file(message.text)
                        await msg.say(file_box)
                elif message.type == MessageType.MESSAGE_TYPE_MINI_PROGRAM:
                    mini_program_json = json.loads(message.text)
                    mini_program = MiniProgram.create_from_json(mini_program_json)
                    await msg.say(mini_program)
                elif message.type == MessageType.MESSAGE_TYPE_URL:
                    url_link = UrlLink.create(message.text, title=None, thumbnail_url=None, description=None)
                    await msg.say(url_link)
                await asyncio.sleep(1)

            except:
                continue
