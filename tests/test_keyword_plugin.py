import pytest
from wechaty import MessageType
from antigen_bot.plugins.keyword_reply import KeyWordReplyPlugin, Rule, Reply


@pytest.mark.asyncio
async def test_config():
    """test config file loader"""
    config_file = 'tests/data/keyword_reply.json'
    plugin = KeyWordReplyPlugin(config_file=config_file, command_prefixs='/')
    rules = await plugin._load_rules()
    assert len(rules) == 2


def test_reply():
    """test init Reply object and save reply object"""
    reply = Reply(text='aa')
    assert reply.type == MessageType.MESSAGE_TYPE_TEXT

    reply_dict = reply.to_dict()
    assert reply_dict['text'] == 'aa'
    assert reply_dict['type'] == 'text'

def test_mini_program_reply():
    """test init Reply object and save reply object"""
    reply = Reply(text=dict(title='a', description='b'), type=MessageType.MESSAGE_TYPE_MINI_PROGRAM)
    assert reply.type == MessageType.MESSAGE_TYPE_MINI_PROGRAM

    reply_dict = reply.to_dict()
    payload = reply_dict['text']
    assert isinstance(payload, dict)
    assert payload['title'] == 'a'
    assert reply_dict['type'] == 'mini_program'
