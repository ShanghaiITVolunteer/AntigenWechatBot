import asyncio
import os
from wechaty_puppet import get_logger

from wechaty import Wechaty, RoomInvitation
from antigen_bot.plugins import (
    MessageForwarderPlugin,
    WatchRoomTopicPlugin
)

class WechatyBot(Wechaty):

    async def on_room_invite(self, room_invitation: RoomInvitation) -> None:
        a = ''

if __name__ == "__main__":
    os.environ['WECHATY_LOG'] = 'silly'
    bot = WechatyBot()
    bot.use([
        MessageForwarderPlugin(),
        WatchRoomTopicPlugin()
    ])
    asyncio.run(bot.start())
