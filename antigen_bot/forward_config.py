"""Define the forward configuration"""
from __future__ import annotations
from abc import abstractmethod
from typing import List, Literal, Tuple, Union
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from pandas import ExcelFile, DataFrame, Series
from wechaty import Contact, ContactPayload, Room, RoomPayload


from antigen_bot.matcher import Matcher, MatcherOption


class ConfigStorer:
    
    @abstractmethod
    def add(self, group: str, forwarder: Matcher, receiver: Matcher) -> None:
        """save the config"""
        raise NotImplementedError
    
    @abstractmethod
    def remove(self, forwarder: Matcher, receiver: Matcher) -> None:
        """remove the config"""
        raise NotImplementedError
    
    @abstractmethod
    def get(self, group: str) -> Tuple[List[Matcher], List[Matcher]]:
        """get the forwarders and receivers by the group name"""
        raise NotImplementedError


class ExcelConfigStorer(ConfigStorer):
    def __init__(self, excel_file: str, engine: str = 'openpyxl') -> None:
        self.excel_file = excel_file
        self.engine = engine

    def all_groups(self) -> List[str]:
        excel = ExcelFile(self.excel_file, engine=self.engine)
        return excel.sheet_names
    
    def _add_record(self, group: str, matcher: Matcher, type: Literal['forwarder', 'receiver']) -> None:
        excel = ExcelFile(self.excel_file, engine=self.engine)
        sheet: DataFrame = excel.parse(group)
        sheet.add(Series())
        sheet.to_excel(self.excel_file, engine=self.engine)

    def add(self, group: str, forwarder: Matcher, receiver: Matcher):
        forwarders, receivers = self.get(group)
        forwarder_md5, receiver_md5 = forwarder.md5(), receiver.md5()

        if not [_forwarder for _forwarder in forwarders if _forwarder.md5() == forwarder_md5]:
            self._add_record(group, forwarder, 'forwarder')

        if not [_receiver for _receiver in receivers if _receiver.md5() == receiver_md5]:
            self._add_record(group, receiver, 'receiver')
 

        

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

@dataclass_json
@dataclass
class Conv2ConvsConfig:
    """Conversation to conversations configuration"""
    name: str
    admins: Dict[str, Conversation] = field(default_factory=dict)
    target_conversations: Dict[str, Conversation] = field(default_factory=dict)

    def is_admin(self, conversation_id: str) -> bool:
        """check if the conversation is admin conversation

        Args:
            conversation_id (str): the id of Room or Contact

        Returns:
            bool: if the conversation is admin conversation
        """
        return str(conversation_id) in self.admins

    def get_target_conversation(self, name_or_no: Optional[str] = None) -> List[Conversation]:
        """get the target conversation object

        Args:
            name_or_no (str): the name or number of the target conversation

        Returns:
            Optional[Conversation]: the target conversation object
        """
        conversations: List[Conversation] = list(self.target_conversations.values())

        if name_or_no:
            name_or_no = str(name_or_no)
            conversations = [conversation for conversation in conversations if str(conversation.name) == name_or_no or str(conversation.no) == name_or_no]
        return conversations

    def get_names_or_nos(self) -> List[str]:
        """get the names or numbers of the target conversations

        Returns:
            List[str]: the names or numbers of the target conversations
        """
        names_or_nos = set()
        for conversation in self.target_conversations.values():
            names_or_nos.add(conversation.name)

        for conversation in self.target_conversations.values():
            names_or_nos.add(conversation.no)

        return [str(item) for item in names_or_nos]
    
    def add_admin(self, conversation: Conversation) -> None:
        """add the conversation to admin conversation

        Args:
            conversation (Conversation): the conversation object
        """
        self.admins[conversation.id] = conversation


class ConfigFactory:
    """Config Factory"""
    def __init__(self, config_file: str) -> None:
        self.file = config_file
        self.md5 = self._get_md5()

        self.configs: List[Conv2ConvsConfig] = []
    
    def _get_md5(self) -> str:
        """get the md5 sum of the configuration file"""
        with open(self.file, 'rb') as f:
            data = f.read()
            md5 = hashlib.md5(data).hexdigest()
        return md5
    
    def instance(self) -> List[Conv2ConvsConfig]:
        """get the instance the configuration"""
        if not self.configs or self._get_md5() != self.md5:
            self.configs = load_from_excel(self.file)
        return self.configs