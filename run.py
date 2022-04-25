import asyncio
from wechaty import Wechaty, WechatyOptions, WechatyPluginOptions
from antigen_bot.plugins import (
    MessageForwarderPlugin, OnCallNoticePlugin
)


if __name__ == "__main__":
    options = WechatyOptions(
        port=int(os.environ.get('PORT', 8004))
    )
    bot = Wechaty(options)
    bot.use([
        MessageForwarderPlugin(
            config_file='.wechaty/message_forwarder_v2.json'
        ),
        OnCallNoticePlugin(
            config_file='.wechaty/on_call_notice.json'
        ),
        Conv2ConvsPlugin(config_file='.wechaty/conv2convs_config.xlsx'),
        DynamicCodePlugin(),
        HealthCheckPlugin(options=HealthCheckPluginOptions(final_failure_handler=final_failure_handler))
    ])
    asyncio.run(bot.start())
