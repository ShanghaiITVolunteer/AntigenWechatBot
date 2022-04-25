from antigen_bot.plugins.dynamic_code import DynamicCodePlugin


import pytest

@pytest.fixture
def plugin():
    """basic plugin"""
    code_file = './tests/data/dynamic_code.xlsx'
    return DynamicCodePlugin(code_file=code_file, max_length=6)

@pytest.mark.asyncio
def test_gen_dynamic_code(plugin: DynamicCodePlugin):
    """test the gen_dynamic_code function"""
    code = plugin.gen_dynamic_code()
    assert isinstance(code, int)
    assert 100 <= code <= 999


@pytest.mark.asyncio
async def test_check_code(plugin: DynamicCodePlugin):
    """test the check_code function"""
    codes = plugin.gen_dynamic_code_file(hours=2, count=2)
    assert len(codes) == 2

    code = codes[0]['code']
    assert plugin.is_valid_code(code)
    assert plugin.is_valid_code(str(code))
