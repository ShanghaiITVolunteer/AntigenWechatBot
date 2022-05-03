from __future__ import annotations
from antigen_bot.matcher import (
    Matcher,
    MatcherOption
)


def test_init_matcher_option():
    """test matcher option"""
    matcher_opiton = MatcherOption(text='room-id', type='id_or_name')
    assert matcher_opiton.text == 'room-id'

def test_load_matcher_option():
    """test load matcher option from file"""


def test_matcher_md5():
    """test compute md5 of matcher option"""
    matcher_option = MatcherOption(text='room-id', type='id_or_name')
    md5_string = matcher_option.md5()
    assert md5_string is not None

    new_matcher_option = MatcherOption(text='room-id', type='id_or_name')
    new_md5_string = new_matcher_option.md5()

    assert new_md5_string == md5_string


def test_matcher_equal():
    """test the equal for matcher class"""
    matcher_option = MatcherOption(text='room-id', type='id_or_name')
    matcher_1 = Matcher(matcher_option)
    matcher_2 = Matcher(matcher_option)

    matcher_3 = Matcher([matcher_option, matcher_option])

    assert matcher_1 == matcher_2
    assert matcher_1 == matcher_3
