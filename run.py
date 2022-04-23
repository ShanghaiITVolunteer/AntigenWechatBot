import asyncio
from wechaty import Wechaty, WechatyOptions, WechatyPluginOptions
from antigen_bot.plugins import (
    MessageForwarderPlugin,
)
from antigen_bot.plugins.conv2convs import Conv2ConvsPlugin


if __name__ == "__main__":
    options = WechatyOptions(
        port=5003
    )
    bot = Wechaty(options)
    bot.use([
        # MessageForwarderPlugin(
        #     config_file='.wechaty/message_forwarder_v2.json'
        # ),
        # MessageForwarderPlugin(
        #     options=WechatyPluginOptions(name='MessageForwarderTestPlugin'),
        #     config_file='.wechaty/message_forwarder_test.json'
        # ),
        Conv2ConvsPlugin(config_file='.wechaty/conv2convs_config.xlsx')
    ])
    asyncio.run(bot.start())
