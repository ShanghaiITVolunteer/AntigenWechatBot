"""Unit test for room2rooms.py"""
from typing import List
from antigen_bot.plugins.conv2convs import Conv2ConvsConfig, load_from_excel


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
