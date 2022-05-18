

from antigen_bot.plugins.platform import PlatformPlugin

def test_get_info():
    plugin = PlatformPlugin()
    info = plugin.get_platform_info()
    assert not not info
