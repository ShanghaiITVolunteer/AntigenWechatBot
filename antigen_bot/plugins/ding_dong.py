"""basic ding-dong bot for the wechaty plugin"""
import asyncio
from typing import Optional
from asyncio import Event
from quart import Quart, jsonify

from wechaty import Message, Wechaty, WechatyPluginOptions
from wechaty.plugin import WechatyPlugin
from wechaty_puppet import get_logger

from antigen_bot.message_controller import MessageController



class DingDongPlugin(WechatyPlugin):
    """DingDong Plugin"""
    def __init__(self, options: Optional[WechatyPluginOptions] = None):
        super().__init__(options)
        
        self.event = Event()
        self.is_init = False
        self.logger = get_logger('messages', file='.wechaty/messages.log')

    async def init_plugin(self, wechaty: Wechaty) -> None:
        wechaty.on('dong', self.on_dong)

    async def on_dong(self, *args, **kwargs) -> None:
        """listen dong event"""
        if not self.is_init:
            return
        self.event.set()

    @MessageController.instance().may_disable_message
    async def on_message(self, msg: Message) -> None:
        """listen message event"""
        talker = msg.talker()
        text = msg.text()
        if msg.room():
            topic = await msg.room().topic()
            if topic.startswith('嘉怡') and topic.endswith('号楼组群'):
                return
            if topic == '嘉怡志愿者群':
                return

            self.logger.info(msg)
            return
        self.logger.info(msg)

        if text == 'ding':
            MessageController.instance().disable_all_plugins(msg)
            await talker.say('dong')

    async def blueprint(self, app: Quart) -> None:
        @app.route('/ding')
        async def listence_ding():
            if not self.is_init:
                self.event._loop = asyncio.get_event_loop()
                self.is_init = True
            
            await self.bot.puppet.ding()
            if self.event.is_set():
                self.event.clear()
            await self.event.wait()
            self.event.clear()
            return jsonify(dict(code=200, msg='dong'))
