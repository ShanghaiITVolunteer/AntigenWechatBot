import asyncio
import os
import sys

from wechaty import Wechaty, WechatyOptions, WechatyPluginOptions

from dotenv import load_dotenv

from antigen_bot.plugins import (
    MessageForwarderPlugin,
)
from antigen_bot.plugins.conv2convs import Conv2ConvsPlugin
from antigen_bot.plugins.health_check import HealthCheckPlugin, HealthCheckPluginOptions
from antigen_bot.plugins.dynamic_code import DynamicCodePlugin
from antigen_bot.plugins.ding_dong import DingDongPlugin

async def final_failure_handler(*args, **kwargs):
    sys.exit()


if __name__ == "__main__":
    load_dotenv()
    options = WechatyOptions(
        port=int(os.environ.get('PORT', 8004)),
    )
    bot = Wechaty(options)
    dynamic_plugin = DynamicCodePlugin()
    bot.use([
        MessageForwarderPlugin(
            config_file='.wechaty/message_forwarder_v2.json'
        ),
        MessageForwarderPlugin(
            options=WechatyPluginOptions(name='MessageForwarderTestPlugin'),
            config_file='.wechaty/message_forwarder_test.json'
        ),
        Conv2ConvsPlugin(config_file='.wechaty/conv2convs_config.xlsx', dynamic_code_plugin=dynamic_plugin),
        dynamic_plugin,
        HealthCheckPlugin(options=HealthCheckPluginOptions(final_failure_handler=final_failure_handler)),
        DingDongPlugin(),
    ])
    asyncio.run(bot.start())
