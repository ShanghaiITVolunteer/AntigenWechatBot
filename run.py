import asyncio
from wechaty import Wechaty, WechatyOptions, WechatyPluginOptions
from antigen_bot.plugins import (
    MessageForwarderPlugin, OnCallNoticePlugin
)


if __name__ == "__main__":
    options = WechatyOptions(
        port=5005
    )
    bot = Wechaty(options)
    bot.use([
        MessageForwarderPlugin(
            config_file='.wechaty/message_forwarder_v2.json'
        ),
        OnCallNoticePlugin(
            options=WechatyPluginOptions(name='Jiayioncalltest'),
            config_file='.wechaty/qun_forwarder.json'
        )
    ])
    asyncio.run(bot.start())
