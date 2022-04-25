"""basic ding-dong bot for the wechaty plugin"""
from wechaty import Message 
from wechaty.plugin import WechatyPlugin


class DingDongPlugin(WechatyPlugin):
    """DingDong Plugin"""
    
    async def on_message(self, msg: Message) -> None:
        """listen message event"""
        talker = msg.talker()
        text = msg.text()
        if msg.room():
            return

        if text == 'ding':
            await talker.say('dong')