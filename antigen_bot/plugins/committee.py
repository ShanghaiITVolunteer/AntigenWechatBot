"""Committee Plugin which provide more"""
from typing import Optional

from wechaty import Message, WechatyPluginOptions
from wechaty.plugin import WechatyPlugin


class CommitteePlugin(WechatyPlugin):
    """居委会插件"""
    def __init__(self, options: Optional[WechatyPluginOptions] = None, command_prefix: str = '#'):
        super().__init__(options)

        self.command_prefix = command_prefix
        
    async def on_message(self, msg: Message) -> None:
        """listen message event"""
