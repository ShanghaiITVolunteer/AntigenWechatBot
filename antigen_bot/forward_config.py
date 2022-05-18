"""Define the forward configuration"""
from __future__ import annotations
from datetime import datetime
import os
from typing import Dict, Optional, List, Set
import hashlib
from dataclasses import dataclass, field

from pandas import DataFrame, read_excel
from dataclasses_json import dataclass_json

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


def load_from_excel(file: str) -> List[Conv2ConvsConfig]:
    """load the configuration from excel file"""
    # 1. load configuration from excel file
    group_df: DataFrame = read_excel(file, sheet_name='group')
    admin_df: DataFrame = read_excel(file, sheet_name='admins')

    # 2. build the configuration
    configs: List[Conv2ConvsConfig] = []
    group_names = list(set(group_df.group_name))

    for group_name in group_names:
        config: Conv2ConvsConfig = Conv2ConvsConfig(name=group_name)

        group_df_group_name = group_df[group_df.group_name == group_name]
        for _, row in group_df_group_name.iterrows():
            config.target_conversations[str(row.id)] = Conversation(
                name=row['name'],
                id=row['id'],
                type=row['type'],
                no=row['no']
            )
        admin_df_group_name = admin_df[admin_df.group_name == group_name]
        for _, row in admin_df_group_name.iterrows():
            config.admins[str(row.id)] = Conversation(
                name=row['name'],
                id=row['id'],
                type=row['type'],
                no=row['no']
            )
        configs.append(config)
    return configs


class ConfigFactory:
    """Config Factory"""
    def __init__(self, config_file: str) -> None:
        self.file = config_file
        self.mtime = self._get_mtime()

        self.configs: List[Conv2ConvsConfig] = []
        self._admin_ids = set()
    
    def _get_mtime(self) -> datetime:
        """get the md5 sum of the configuration file"""
        return os.path.getmtime(self.file)
    
    def config_changed(self) -> bool:
        """check that if the config file changes"""
        return self._get_mtime() != self.mtime

    def instance(self) -> List[Conv2ConvsConfig]:
        """get the instance the configuration"""
        if not self.configs or self.config_changed():
            self.configs = load_from_excel(self.file)
        return self.configs
    
    def get_admin_ids(self) -> Set[str]:
        # 1. return the cached admin ids
        if not self.config_changed() and len(self._admin_ids) > 0:
            return self._admin_ids
        
        # 2. load admin ids
        self._admin_ids.clear()
        for config in self.instance():
            for admin_id in config.admins.keys():
                self._admin_ids.add(admin_id)
            
        return self._admin_ids
