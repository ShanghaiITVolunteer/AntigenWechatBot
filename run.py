import asyncio
import os
from wechaty_puppet import get_logger

from wechaty import Wechaty, RoomInvitation, WechatyOptions
from antigen_bot.plugins import (
    MessageForwarderPlugin,
    WatchRoomTopicPlugin,
    InfoDownloaderPlugin
)

class WechatyBot(Wechaty):

    async def on_room_invite(self, room_invitation: RoomInvitation) -> None:
        a = ''

if __name__ == "__main__":
    os.environ['WECHATY_LOG'] = 'silly'
    options = WechatyOptions(
        port=5003
    )
    bot = WechatyBot(options)
    bot.use([
        MessageForwarderPlugin(),
        WatchRoomTopicPlugin(),
        InfoDownloaderPlugin()
    ])
    asyncio.run(bot.start())
