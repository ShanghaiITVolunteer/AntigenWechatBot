""""""
import os
import re
from typing import (
    Dict, Optional, List, Set, Tuple, Union
)
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

from antigen_bot.forward_config import Conversation, ConfigFactory
from antigen_bot.utils import remove_at_info
from antigen_bot.message_controller import MessageController


def split_number_and_words(text: str, pretrained_numbers: Set[str]) -> Tuple[List[str], List[str]]:
    """split_number_and_words with pretrained_numbers

    Args:
        text (str): the source of numbers
        pretrained_numbers (Set[str]): the pretrained numbers

    Returns:
        Tuple[List[str], List[str]]: the result of numbers and words
    """
    # 1. match the: #3-8 pattern
    pattern = '[ ]?[0-9]+[ ]?-[ ]?[0-9]+'
    result = re.findall(pattern, text)
    if result:
        source_text: str = result[0]
        number_range = [int(item) for item in source_text.split('-')]
        numbers: List[str] = [str(item) for item in range(number_range[0], number_range[1] + 1)]
        words = text.replace(source_text, '').strip()
        return numbers, [words]
 
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
        config_file: Optional[str] = None,
        expire_seconds: int = 60,
        command_prefix: str = '',
        trigger_with_at: bool = True,
    ) -> None:
        """init params for conversations to conversations configuration

        Args:
            options (Optional[WechatyPluginOptions], optional): default wechaty plugin options. Defaults to None.
            config_file (str, optional): _description_. Defaults to .wechaty/<PluginName>/config.xlsx.
            expire_seconds (int, optional): start to forward. Defaults to 60.
            command_prefix (str, optional): . Defaults to ''.
            trigger_with_at (bool, optional): _description_. Defaults to True.
        """
        super().__init__(options)

        self.cache_dir = f'.wechaty/{self.name}'
        self.file_cache_dir = f'{self.cache_dir}/file'
        os.makedirs(self.file_cache_dir, exist_ok=True)

        # 2. save the log info into <plugin_name>.log file
        log_file = os.path.join(self.cache_dir, 'log.log')
        self.logger = get_logger(self.name, log_file)
        
        # 3. save the admin status
        self.admin_status: Dict[str, List[Conversation]] = {}

        self.config_factory = ConfigFactory(config_file)
        self.command_prefix = command_prefix

        self.trigger_with_at = trigger_with_at

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
        if msg.type() in [MessageType.MESSAGE_TYPE_IMAGE, MessageType.MESSAGE_TYPE_VIDEO, MessageType.MESSAGE_TYPE_ATTACHMENT]:
            file_box = await msg.to_file_box()
            file_path = os.path.join(self.file_cache_dir, file_box.name)

            await file_box.to_file(file_path, overwrite=True)
            file_box = FileBox.from_file(file_path)

        for conversation in conversations:
            if conversation.type == 'Room':
                forwarder_target = await self.bot.Room.load(conversation.id)
            elif conversation.type == 'Contact':
                forwarder_target = await self.bot.Contact.load(conversation.id) 
            else:
                continue
            
            # TODO: 转发图片貌似还是有些问题
            if file_box:
                await forwarder_target.say(file_box)

            # 如果是文本的话，是需要单独来转发
            elif msg.type() == MessageType.MESSAGE_TYPE_TEXT:
                await forwarder_target.say(msg.text())

            elif forwarder_target:
                await msg.forward(forwarder_target)

    @MessageController.instance().may_disable_message
    async def on_message(self, msg: Message) -> None:
        talker = msg.talker()
        room: Optional[Room] = msg.room()

        conv: Union[Room, Contact] = room or talker

        # 2. 判断是否是自己发送的消息
        if talker.contact_id == msg.is_self():
            return
        
        # 3. check if is admin 
        if not await self.config_factory.is_admin(conv=conv):
            return
        
        if room and self.trigger_with_at:
            # 判断机器人是否有被艾特
            if not await msg.mention_self():
                return
        
        text = msg.text()
        if room:
            conversation_id = room.room_id
        else:
            conversation_id = talker.contact_id

        # at 条件触发
        if conversation_id not in self.admin_status and self.trigger_with_at:
            mention_self = await msg.mention_self()
            if not mention_self:
                return
            text = remove_at_info(text=text)

        if conversation_id in self.admin_status:
            await self.forward_message(msg, conversation_id=conversation_id)
            self.admin_status.pop(conversation_id)
            return

        # filter the target conversations

        if text.startswith(self.command_prefix):
            # parse token & command
            text = text[len(self.command_prefix):]
            text = text[text.index('#') + 1:].strip()

            receivers = self.config_factory.get_receivers(conv)
            if not receivers:
                return

            self.admin_status[conversation_id] = receivers

            if text:
                # set the words to the message
                msg.payload.text = text
                await self.forward_message(msg, conversation_id=conversation_id)
                self.admin_status.pop(conversation_id)