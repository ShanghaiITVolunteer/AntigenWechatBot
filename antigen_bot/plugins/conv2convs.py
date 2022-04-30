""""""
import os
from typing import (
    Dict, Optional, List, Set, Tuple, Union
)
from dataclasses import dataclass, field
from wechaty import (
    Contact,
    FileBox,
    MessageType,
    WechatyPlugin,
    Room,
    Message,
    WechatyPluginOptions
)
from wechaty_puppet import get_logger
from dataclasses_json import dataclass_json
import pandas as pd
from pandas import DataFrame

from antigen_bot.plugins.dynamic_authory import DynamicAuthorisePlugin


@dataclass_json
@dataclass
class Conversation:
    """Room or Contact Configuraiton"""
    name: str
    id: str
    type: str = 'Room'
    no: str = ''

    def info(self):
        """get the simple info"""
        return f'[{self.type}]\t名称：{self.name}\t\t编号：[{self.id}]'

@dataclass_json
@dataclass
class Conv2ConvsConfig:
    """Conversation to conversations configuration"""
    name: str
    admins: Dict[str, Conversation] = field(default_factory=dict)
    target_conversations: Dict[str, Conversation] = field(default_factory=dict)

    def is_admin(self, conversation_id: str) -> bool:
        """check if the conversation is admin conversation

        Args:
            conversation_id (str): the id of Room or Contact

        Returns:
            bool: if the conversation is admin conversation
        """
        return str(conversation_id) in self.admins
    
    def get_target_conversation(self, name_or_no: Optional[str] = None) -> List[Conversation]:
        """get the target conversation object

        Args:
            name_or_no (str): the name or number of the target conversation

        Returns:
            Optional[Conversation]: the target conversation object
        """
        conversations: List[Conversation] = list(self.target_conversations.values())

        if name_or_no:
            name_or_no = str(name_or_no)
            conversations = [conversation for conversation in conversations if str(conversation.name) == name_or_no or str(conversation.no) == name_or_no]
        return conversations

    def get_names_or_nos(self) -> List[str]:
        """get the names or numbers of the target conversations

        Returns:
            List[str]: the names or numbers of the target conversations
        """
        names_or_nos = set()
        for conversation in self.target_conversations.values():
            names_or_nos.add(conversation.name)

        for conversation in self.target_conversations.values():
            names_or_nos.add(conversation.no)

        return [str(item) for item in names_or_nos]


class ConfigFactory:
    """Config Factory"""
    def __init__(self, config_file: str) -> None:
        self.file = config_file

        self.configs: List[Conv2ConvsConfig] = []

    """
    bigbrother update：romove the md5 related...
    def _get_md5(self) -> str:
        get the md5 sum of the configuration file
        with open(self.file, 'rb') as f:
            data = f.read()
            md5 = hashlib.md5(data).hexdigest()
        return md5
    """

    def instance(self) -> List[Conv2ConvsConfig]:
        """get the instance the configuration
         or self._get_md5() != self.md5"""
        if not self.configs:
            self.configs = load_from_excel(self.file)
        return self.configs


def load_from_excel(file: str) -> List[Conv2ConvsConfig]:
    """load the configuration from excel file"""
    # 1. load configuration from excel file
    group_df: DataFrame = pd.read_excel(file, sheet_name='group')
    admin_df: DataFrame = pd.read_excel(file, sheet_name='admins')

    # 2. build the configuration
    configs: List[Conv2ConvsConfig] = []
    group_names = list(set(group_df.group_name))

    for group_name in group_names:
        config: Conv2ConvsConfig = Conv2ConvsConfig(name=group_name)

        group_df_group_name = group_df[group_df.group_name == group_name]
        for _, row in group_df_group_name.iterrows():
            config.target_conversations[str(row.id)] = Conversation(
                name=row['name'],
                id=row['id'],
                type=row['type'],
                no=row['no']
            )
        admin_df_group_name = admin_df[admin_df.group_name == group_name]
        for _, row in admin_df_group_name.iterrows():
            config.admins[str(row.id)] = Conversation(
                name=row['name'],
                id=row['id'],
                type=row['type'],
                no=row['no']
            )
        configs.append(config)
    return configs


def split_number_and_words(text: str, pretrained_numbers: Set[str]) -> Tuple[List[str], List[str]]:
    """split_number_and_words with pretrained_numbers

    Args:
        text (str): the source of numbers
        pretrained_numbers (Set[str]): the pretrained numbers

    Returns:
        Tuple[List[str], List[str]]: the result of numbers and words
    """
    numbers, words = [], []
    for token in text.split():
        if not token:
            continue
        if token in pretrained_numbers:
            numbers.append(token)
        else:
            words.append(token)
    return numbers, words


class Conv2ConvsPlugin(WechatyPlugin):
    """
    功能点：
        1. 当被邀请入群，则立马同意，同时保存其相关信息。
        2. 如果是私聊的消息，则直接转发给该用户邀请机器人进入的所有群聊当中
    bigbrother updates：
        更改触发校验的dynamic_code机制为dynamic_authority机制
    """
    def __init__(
        self,
        options: Optional[WechatyPluginOptions] = None,
        config_file: str = '.wechaty/conv2convs.xlsx',
        expire_seconds: int = 60,
        command_prefix: str = '#',
        trigger_with_at: bool = True,
        forward_none_command_message: bool = False,
        say_forward_help_info_to_talker: bool = True,
        dynamic_plugin: Optional[DynamicAuthorisePlugin] = None,) -> None:
        super().__init__(options)
        # 1. init the configs file

        # 2. save the log info into <plugin_name>.log file
        log_file = os.path.join('.wechaty', self.name + '.log')
        self.logger = get_logger(self.name, log_file)
        self.expire_seconds = expire_seconds
        
        # 3. save the admin status
        self.admin_status: Dict[str, List[Conversation]] = {}

        self.config_factory = ConfigFactory(config_file)
        self.command_prefix = command_prefix
        self.forward_none_command_message = forward_none_command_message
        self.say_forward_help_info_to_talker = say_forward_help_info_to_talker

        self.trigger_with_at = trigger_with_at
        self.at_prefix_info: Dict[str, str] = {}

        self._rooms: List[Room] = []
        self._contacts: List[Contact] = []

        self.dynamic_plugin = dynamic_plugin


    async def get_room(self, id_or_name) -> Optional[Room]:
        """get the room by id or name"""

        # 1. init the cached room data
        if not self._rooms:
            self._rooms = await self.bot.Room.find_all()
            for room in self._rooms:
                await room.ready()

        # 2. search the room with cached data
        for room in self._rooms:
            if room.room_id == id_or_name or room.payload.topic == id_or_name:
                return room
        return None

    async def get_contact(self, id_or_name: str) -> Optional[Contact]:
        """get the contact from cache or from wechat

        Args:
            id_or_name (str): the id or name of contact

        Returns:
            Optional[Contact]: the contact object
        """
        # 1. init the contact data
        if not self._contacts:
            self._contacts = await self.bot.Contact.find_all()
            for contact in self._contacts:
                await contact.ready()

        # 2. search the contact with cached data
        for contact in self._contacts:
            if contact.contact_id == id_or_name:
                return contact
            name_or_alias = contact.payload.alias or contact.payload.name
            if name_or_alias == id_or_name:
                return contact

        return None

    async def remove_at_info(self, text: str, room_id: str) -> str:
        """get the clear message, remove the command prefix and at"""

        if not self.trigger_with_at:
            return text
        
        if room_id not in self.at_prefix_info:
            split_chars = ['\u2005', '\u0020']
            while text.startswith('@'):
                text = text.strip()
                for char in split_chars:
                    tokens = text.split(char)
                    if len(tokens) > 1:
                        tokens = [token for token in text.split(char) if not token.startswith('@')]
                        text = char.join(tokens)
                    else:
                        text = ''.join(tokens)

        return text

    async def forward_message(self, msg: Message, conversation_id: str):
        """forward the message to the target conversations

        Args:
            msg (Message): the message to forward
            conversation_id (str): the id of conversation
        """
        # 1. get the type of message
        conversations = self.admin_status.get(conversation_id, [])
        if not conversations:
            return

        file_box = None
        if msg.type() == MessageType.MESSAGE_TYPE_IMAGE:
            file_box = await msg.to_file_box()
            file_path = '.wechaty/' + file_box.name
            await file_box.to_file(file_path, overwrite=True)
            file_box = FileBox.from_file(file_path)

        for conversation in conversations:
            forwarder_target: Optional[Union[Room, Contact]] = None

            if conversation.type == 'Room':
                forwarder_target = await self.get_room(conversation.id or conversation.name)
            elif conversation.type == 'Contact':
                forwarder_target = await self.get_contact(conversation.id or conversation.name)

            if file_box:
                await forwarder_target.say(file_box)

            # 如果是文本的话，是需要单独来转发
            elif msg.type() == MessageType.MESSAGE_TYPE_TEXT and forwarder_target:
                await forwarder_target.say(msg.text())

            elif forwarder_target:
                await msg.forward(forwarder_target)

    async def on_message(self, msg: Message) -> None:
        talker = msg.talker()
        room: Optional[Room] = msg.room()

        # 2. 判断是否是自己发送的消息
        if talker.contact_id == self.bot.user_self().contact_id:
            return
        
        # 3. 如果不是群消息的话，就直接返回
        if not room:
            return

        text = msg.text()
        conversation_id = talker.contact_id + room.room_id

        #判断是否管理员授权信息
        if await msg.mention_self() and len(await msg.mention_list()) > 1:
            if talker.contact_id not in self.dynamic_plugin.get_authoriers():
                return
            contact_ids = [contact.contact_id for contact in await msg.mention_list()]
            contact_ids.remove(self.bot.user_self().contact_id)
            self.dynamic_plugin.authorise(contact_ids)
            await room.say("授权完毕，授权期至今日夜12点", [talker.contact_id])
            return

        # at 条件触发
        if conversation_id not in self.admin_status and self.trigger_with_at:
            mention_self = await msg.mention_self()
            if not mention_self:
                return

            if not self.dynamic_plugin.is_valid(talker.contact_id):
                await room.say('今天您不是排班志愿者，无权转发，切勿骚扰机器人。', [talker.contact_id])
                return

            text = await self.remove_at_info(text=text, room_id=room.room_id)

        configs: List[Conv2ConvsConfig] = self.config_factory.instance()

        # 1. 判断是否是群转发的相关配置
        target_configs: List[Conv2ConvsConfig] = [config for config in configs if config.is_admin(room.room_id)]
        if not target_configs:
            return

        if len(target_configs) > 1:
            error_info = '该群或该用户存在多份配置，请联系运营人员重新配置'
            self.logger.error(error_info)
            if room:
                self.logger.error(room)
            else:
                self.logger.error(talker)
            for target_config in target_configs:
                self.logger.info(target_config)

            return

        config = target_configs[0]
        # 2. 如果保存的有 admin status，则直接转发消息
        if conversation_id in self.admin_status:
            await self.forward_message(msg, conversation_id=conversation_id)
            self.admin_status.pop(conversation_id)
            return

        target_conversations = []

        # filter the target conversations
        if text.startswith(self.command_prefix):

            if len(text.split('#')) != 2:
                await msg.say('检查到格式错误，请按照规范输入，格式为\n@AntigenBot #[群号] [群号] [你想说的话]')
                return
            # parse token & command
            text = text[len(self.command_prefix):]

            text = text[text.index('#') + 1:].strip()

            numbers, words = split_number_and_words(text, config.get_names_or_nos())
            for name_or_no in numbers:
                target_conversations.extend(config.get_target_conversation(name_or_no))

            self.admin_status[conversation_id] = target_conversations

            if words:
                # set the words to the message
                msg.payload.text = ' '.join(words)
                await self.forward_message(msg, conversation_id=conversation_id)
                self.admin_status.pop(conversation_id)
        
    async def say_forward_help_info(self, msg: Message):
        """say frowarder help info to the talker

        Args:
            conversation (Union[Room, Contact]): the source of the 
        """
        talker = msg.talker()
        room: Optional[Room] = msg.room()
        conversation_id = talker.contact_id + room.room_id if room else talker.contact_id

        if conversation_id not in self.admin_status:
            return

        help_infos = []
        for target_conversation in self.admin_status.get(conversation_id, []):
            help_infos.append(target_conversation.info())

        if not help_infos:
            info = '机器人未检测到任何转发群信息'
        else:
            info = '机器人将会把消息转发到如下群中：\n' + '\n'.join(help_infos)

        await msg.say(info)
