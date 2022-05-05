import pytest
from datetime import datetime
from antigen_bot.plugins.dynamic_authorization import DynamicAuthorizationPlugin



@pytest.fixture
def plugin() -> DynamicAuthorizationPlugin:
    """basic plugin"""
    config_file = './tests/data/dynamic_authorization.json'
    conv2conv_file = './tests/data/conv2convs_config.xlsx'
    return DynamicAuthorizationPlugin(config_file=config_file, conv_config_file=conv2conv_file)

@pytest.mark.asyncio
def test_dynamic_authorize(plugin: DynamicAuthorizationPlugin):
    """test the gen_dynamic_code function"""
    contact_id = 'test_id'
    assert not plugin.is_valid(contact_id)

    today = datetime.today()
    date_string = today.strftime('%Y-%m-%d')
    plugin.authorize(date_string, [contact_id])
    assert plugin.is_valid(contact_id)

    plugin.unauthorize(date_string, [contact_id])
    assert not plugin.is_valid(contact_id)

