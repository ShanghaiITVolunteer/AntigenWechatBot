"""Unit test for room2rooms.py"""
import os
from typing import List
import pytest
from antigen_bot.plugins.conv2convs import (
    Conv2ConvsPlugin,
    split_number_and_words
)
from antigen_bot.plugins.dynamic_authorization import (
    Conv2ConvsConfig,
    load_from_excel
)
from antigen_bot.utils import remove_at_info


def test_config():
    """test the configuration load"""
    file = './tests/data/conv2convs_config.xlsx'
    configs: List[Conv2ConvsConfig] = load_from_excel(file=file)
    assert len(configs) == 1

    config: Conv2ConvsConfig = configs[0]
    assert config.name == '测试小区'

    assert len(config.admins) == 3
    assert len(config.target_conversations) == 13

    assert config.is_admin('1101')


def test_multi_config():
    """test the configuration load"""
    file = './tests/data/conv2convs_multi_config.xlsx'
    configs: List[Conv2ConvsConfig] = load_from_excel(file=file)
    assert len(configs) == 2

    config: Conv2ConvsConfig = configs[0]
    assert config.name in ['测试小区-1', '测试小区-2']

    assert len(config.admins) == 3
    assert len(config.target_conversations) == 13

    assert config.is_admin('1101')


@pytest.mark.asyncio
async def test_remove_at_info():
    """test remove at info"""
    file = './tests/data/conv2convs_multi_config.xlsx'
    plugin = Conv2ConvsPlugin(config_file=file)
    at_info = '@AntigenBot hello'
    info = remove_at_info(at_info)
    assert info == 'hello'


@pytest.mark.asyncio
async def test_remove_at_info_with_many_person():
    """test remove at info"""
    file = './tests/data/conv2convs_multi_config.xlsx'
    plugin = Conv2ConvsPlugin(config_file=file)
    at_info = '@AntigenBot\u0020@wj-Mcat\u0020@wj-Mcat\u2005hello'
    info = remove_at_info(at_info)
    assert info == 'hello'


@pytest.mark.asyncio
async def test_remove_at_info_with_command():
    """test remove at info"""
    file = './tests/data/conv2convs_multi_config.xlsx'
    plugin = Conv2ConvsPlugin(config_file=file)
    at_info = '@AntigenBot\u0020#3 hello'
    info = remove_at_info(at_info)
    assert info == '#3 hello'


def test_split_numbers_and_words():
    """split number and words"""

    text = '3 8 你好'
    numbers = ['3', '8']
    numbers, words = split_number_and_words(text, pretrained_numbers=numbers)
    assert numbers == ['3', '8']
    assert words == ['你好']

    text = '3 8 8.3 你好'
    numbers, words = split_number_and_words(text, pretrained_numbers=numbers)
    assert numbers == ['3', '8']
    assert words == ['8.3', '你好']

    numbers = ['3', '8', '8.3']
    numbers, words = split_number_and_words(text, pretrained_numbers=numbers)
    assert numbers == ['3', '8', '8.3']
    assert words == ['你好']

    text = '3-8 您好'
    numbers, words = split_number_and_words(text, [])
    assert numbers == [str(number) for number in range(3, 9)]
    assert words == ['您好']

    text = '3 - 8 您好'
    numbers, words = split_number_and_words(text, [])
    assert numbers == [str(number) for number in range(3, 9)]
    assert words == ['您好']

def test_name_split():
    """test name split"""
    file_name = 'aa.jpg'
    name, file_type = os.path.splitext(file_name)
    assert name == 'aa'
    assert file_type == '.jpg'