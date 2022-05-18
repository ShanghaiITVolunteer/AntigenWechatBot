"""Define the forward configuration"""
from __future__ import annotations
from datetime import datetime
import os
from typing import Dict, Optional, List, Set, Tuple, Union
import hashlib
from dataclasses import dataclass, field

from pandas import DataFrame, read_excel
from dataclasses_json import dataclass_json
from wechaty import Contact, Room

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

    def get_target_conversation(self, conv_id: str) -> List[Conversation]:
        """get the target conversation object

        Args:
            conv_id (str): the id of admin conversation 

        Returns:
            List[Conversation]: the target conversation object
        """
        return self.target_conversations.get(conv_id, [])

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

        self._configs: List[Conv2ConvsConfig] = []
        self._admin_ids = set()
    
    def _get_mtime(self) -> datetime:
        """get the md5 sum of the configuration file"""
        return os.path.getmtime(self.file)
    
    def config_changed(self) -> bool:
        """check that if the config file changes"""
        return self._get_mtime() != self.mtime

    def get_configs(self) -> List[Conv2ConvsConfig]:
        """get the instance the configuration"""
        if not self._configs or self.config_changed():
            self._configs = load_from_excel(self.file)
        return self._configs
    
    def get_admin_ids(self) -> Set[str]:
        # 1. return the cached admin ids
        if not self.config_changed() and len(self._admin_ids) > 0:
            return self._admin_ids
        
        # 2. load admin ids
        self._admin_ids.clear()
        for config in self.get_configs():
            for admin_id in config.admins.keys():
                self._admin_ids.add(admin_id)
            
        return self._admin_ids
    
    async def is_admin(self, conv: Union[Contact, Room]) -> bool:
        admin_ids = self.get_admin_ids()
        if isinstance(conv, Contact):
            return conv.contact_id in admin_ids
        if isinstance(conv, Room):
            return conv.room_id in admin_ids
        raise TypeError(f'conv type is expected with <Contact, Room>, but receive <{type(conv)}>')
    
    async def get_receivers(self, conv: Union[Contact, Room, str]) -> Tuple[List[str], List[str]]:
        """get receivers by conv id

        Args:
            conv (Union[Contact, Room, str]): 
                if is str, it present the id of Contact/Room
                if is Contact, it present the instance of Contact
                if is Room, it present the instance of Room

        Returns:
            Tuple[List[str], List[str]]: List[Room], List[Contact]
        """
        # 1. init the conv data
        if isinstance(Contact):
            conv = conv.contact_id
        elif isinstance(Room):
            conv = conv.room_id
        
        configs = self.get_configs()

        # 2. get room ids & contact ids
        room_ids, contact_ids = [], []
        for config in configs:
            if config.is_admin(conv):
                for conversation in config.get_target_conversation(conv):
                    if conversation.type == 'Contact':
                        contact_ids.append(conversation.id)
                    elif conversation.type == 'Room':
                        room_ids.append(conversation.id)
    
        return room_ids, contact_ids
        

        
                    