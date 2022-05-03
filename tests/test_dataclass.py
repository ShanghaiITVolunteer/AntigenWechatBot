from wechaty_puppet import MessageType
from antigen_bot.plugins.keyword_reply import Reply


def test_enum_init():
    """text enum"""
    data = dict(text='hello', type='text')
    reply = Reply(**data)
    assert reply.type == MessageType.MESSAGE_TYPE_TEXT