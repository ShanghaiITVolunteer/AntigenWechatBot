"""fetch the message with the generator mode"""
from typing import List, Optional
from asyncio import Event

from wechaty import Message, WechatyPluginOptions
from wechaty.plugin import WechatyPlugin


class MessagePlugin(WechatyPlugin):
    """DingDong Plugin"""
    def __init__(self, options: Optional[WechatyPluginOptions] = None):
        super().__init__(options)
        self.event = Event()
        self.message_box: List[Message] = []

    async def fetch_message(self) -> Message:
        """wait for fetching the message"""
        await self.event.wait()
        self.event.clear()
        return self.message

    async def on_message(self, msg: Message) -> None:
        """listen message event"""
        self.message_box.append(msg)
        self.event.set()
