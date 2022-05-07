"""Basic Configuraiton for Bot"""
from __future__ import annotations
from dataclasses import dataclass
from dataclasses_json import dataclass_json


DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


@dataclass_json
@dataclass
class Conversation:
    """Room or Contact Configuraiton"""
    name: str
    id: str
    type: str = 'Room'
    no: str = ''

    def info(self):
        """get the simple info"""
        return f'[{self.type}]\t名称：{self.name}\t\t编号：[{self.id}]'
