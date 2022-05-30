"""basic ding-dong bot for the wechaty plugin"""
import asyncio
from typing import Optional, List
from asyncio import Event
from quart import Quart, jsonify

from wechaty import Message, MessageType, Wechaty, WechatyPluginOptions
from wechaty.plugin import WechatyPlugin
from wechaty_puppet import get_logger

from antigen_bot.message_controller import message_controller
from antigen_bot.utils import remove_at_info



class RepeaterPlugin(WechatyPlugin):
    """Repeater Plugin"""
    def __init__(self, options: Optional[WechatyPluginOptions] = None, room_ids: List[str] = []):
        super().__init__(options)
        
        self.logger = get_logger(self.name, file=f'.wechaty/{self.name}.log')

        self.room_ids = room_ids

    @message_controller.may_disable_message
    async def on_message(self, msg: Message) -> None:
        """listen message event"""
        
        room = msg.room()
        if not room or room.room_id not in self.room_ids:
            return
        
        if not await msg.mention_self() or msg.type() != MessageType.MESSAGE_TYPE_TEXT:
            return
        
        text = remove_at_info(msg.text())

        talker = msg.talker()
        await room.say(text, mention_ids=[talker.contact_id])
        message_controller.disable_all_plugins()