"""Base matcher for finding"""
from __future__ import annotations
import re
from re import Pattern
import json
import hashlib
from inspect import isfunction, iscoroutinefunction
from typing import (
    Union,
    List,
    Optional,
    Literal
)
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from wechaty import ContactPayload, FileBox
from wechaty_plugin_contrib.config import (
    Room,
    Contact,
    Message
)



class Conversation:
    """get info from Contact or Room"""
    def __init__(self, target: Union[Contact, Room, Message]) -> None:
        if isinstance(target, Message):
            self.target = target.room() or target.talker()
        else:
            self.target = target

    def get_id(self) -> str:
        """get the union identifier of target

        Returns:
            str: the union identifier of target
        """
        if isinstance(self.target, Contact):
            return self.target.contact_id
        return self.target.room_id

    async def get_name(self) -> str:
        """get the name of target

        Returns:
            str: the name of target
        """
        await self.target.ready()
        if isinstance(self.target, Contact):
            payload: ContactPayload = self.target.payload
            return payload.alias or payload.name

        return self.target.payload.topic

    async def say(self, msg: Union[FileBox, Message]):
        """send the message to target

        Args:
            msg (Union[FileBox, Message]): the message to send
        """
        if isinstance(msg, FileBox):
            await self.target.say(msg)
        elif isinstance(msg, Message):
            await msg.forward(self.target)


@dataclass_json
@dataclass(init=False)
class MatcherOption:
    """Matcher Option"""
    def __init__(self, text, type, **kwargs) -> None:
        self.text = text
        self.type = type

    text: Optional[str] = None
    type: Literal['id_or_name', 'regex', 'method'] = 'id_or_name'

    async def match(self, target: Conversation) -> bool:
        """match the conversation

        Args:
            target (Conversation): the target conversation

        Returns:
            bool: if match the conversation
        """
        if self.type == 'id_or_name':
            return self.text == target.get_id() or self.text == await target.get_name()
        
        if self.type == 'regex':
            pattern: Pattern = re.Pattern(self.text)
            if pattern.match(target.get_id()) is not None:
                return True
            name = await target.get_name()
            if pattern.match(name) is not None:
                return True
            return False

        if self.type == 'method' and isfunction(self.text):
            if iscoroutinefunction(self.text):
                result = await self.text(target)
            else:
                result = self.text(target)
            return result

        raise ValueError(f'{self.type} is not a valid type, which should be one of [id_or_name, regex, method]')
    
    def union_str(self) -> str:
        """get the union string of matcher option

        Returns:
            str: the union string of matcher option
        """
        if self.type == 'method':
            raise ValueError('method cannot be used in union string')

        return f'{self.type}:{self.text}'
    
    def md5(self) -> str:
        """get the md5 of matcher option

        Returns:
            str: the md5 of matcher option
        """
        present_str = self.union_str()
        return hashlib.md5(present_str.encode(encoding='utf-8')).hexdigest()
    
    def to_dict(self) -> dict:
        """get the dict of matcher option

        Returns:
            str: the dict of matcher option
        """
        return dict(
            text=self.text,
            type=self.type,
            md5=self.md5()
        )

    def __eq__(self, option: object) -> bool:
        if not option or isinstance(option, MatcherOption):
            return False
        return self.union_str() == option.union_str()


class Matcher:
    """handle the Conversation Match logic"""
    def __init__(self, option: Union[MatcherOption, List[MatcherOption]]) -> None:
        if isinstance(option, list):
            self.options = option
        else:
            self.options = [option]
    
    async def match(self, target: Union[Contact, Room, Message, Conversation]) -> bool:
        """match the conversation

        Args:
            target (Union[Contact, Room, Message]): the target conversation

        Returns:
            bool: if match the conversation
        """
        if not isinstance(Conversation):
            conversation: Conversation = Conversation(target)

        for option in self.options:
            result = await option.match(conversation)
            if result:
                return True
        return False
    
    def md5(self) -> str:
        """get the md5 presentation string

        Returns:
            str: the md5 string
        """
        md5_strings = set([option.md5() for option in self.options])
        return ','.join(md5_strings)

    def __eq__(self, other_matcher: object) -> bool:
        if not other_matcher:
            return False
        if not isinstance(other_matcher, Matcher):
            return False

        source_strings = set([option.union_str() for option in self.options])
        other_strings = set([option.union_str() for option in other_matcher.options])

        return len(source_strings - other_strings) == 0 and len(other_strings - source_strings) == 0


def load_matcher_option_from_file(config_file: str) -> List[MatcherOption]:
    """load matcher option from file"""
    with open(config_file, 'r', encoding='utf-8') as file_handler:
        option_dict = json.load(file_handler)
    return [MatcherOption(**option) for option in option_dict]
