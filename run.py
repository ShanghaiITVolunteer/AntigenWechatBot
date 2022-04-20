import asyncio
import os

from wechaty import Wechaty, WechatyOptions
from antigen_bot.plugins import (
    MessageForwarderPlugin,
    # WatchRoomTopicPlugin,
)


if __name__ == "__main__":
    os.environ['WECHATY_LOG'] = 'silly'
    options = WechatyOptions(
        port=5003
    )
    bot = Wechaty(options)
    bot.use([
        MessageForwarderPlugin(),
        # WatchRoomTopicPlugin(),
    ])
    asyncio.run(bot.start())
