import asyncio
from wechaty import Wechaty, WechatyOptions
from antigen_bot.plugins import (
    MessageForwarderPlugin,
)


if __name__ == "__main__":
    options = WechatyOptions(
        port=5003
    )
    bot = Wechaty(options)
    bot.use([
        MessageForwarderPlugin(
            config_file='.wechaty/message_forwarder_v2.json'
        ),
        MessageForwarderPlugin(
            options=WehchatyPluginOptions(name='MessageForwarderTestPlugin'),
            config_file='.wechaty/message_forwarder_test.json'
        )
    ])
    asyncio.run(bot.start())
