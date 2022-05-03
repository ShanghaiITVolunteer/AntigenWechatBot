"""Dynamic Authorization Plugin"""
from __future__ import annotations
import os
import json
from datetime import datetime, timedelta
from typing import (
    Dict,
    Optional,
    List
)
import hashlib
from dataclasses import dataclass, field

from wechaty import (
    WechatyPlugin,
    WechatyPluginOptions,
    Message
)
from wechaty_puppet import get_logger
from dataclasses_json import dataclass_json
import pandas as pd
from pandas import DataFrame

from antigen_bot.utils import remove_at_info

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
    group_df: DataFrame = pd.read_excel(file, sheet_name='group')
    admin_df: DataFrame = pd.read_excel(file, sheet_name='admins')

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



class DynamicAuthorizationPlugin(WechatyPlugin):
    """
    功能点：
        1. 管理员通过同时@bot和要被授权的同群组人员，进行授权（默认授权有效期当天）
        2. 发出转发命令的talker是否在当日授权名单中
        3. 一天之内重复授权，后一次会覆盖前一次
    
    Data Structure:
        {
            'date': ['id', 'id', ...],
        }
    """
    def __init__(
        self,
        options: Optional[WechatyPluginOptions] = None,
        config_file: str = '.wechaty/dynamic_authorise.json',
        conv_config_file: str = '.wechaty/conv2convs.xlsx'
    ):
        super().__init__(options)
        # 1. init the configs file
        self.config_file = config_file

        # 2. save the log info into <plugin_name>.log file
        log_file = os.path.join('.wechaty', self.name + '.log')
        self.logger = get_logger(self.name, log_file)

        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        self.config_factory = ConfigFactory(conv_config_file)
    
    def _load_config(self) -> Dict[str, List[str]]:
        """load the data from config file"""
        if not os.path.exists(self.config_file):
            self.logger.error('configuration file not found: %s', self.config_file)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)

        with open(self.config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    def _save_config(self, config):
        """save the data to config file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False)
    
    def authorize(self, date: str, contact_ids: List[str]):
        """authorize the talkers"""

        config = self._load_config()

        if date not in config:
            config[date] = []

        for contact_id in contact_ids:
            if contact_id not in config[date]:
                config[date].append(contact_id)
        self._save_config(config)

    def unauthorize(self, date: str, contact_ids: List[str]):
        """authorize the talkers"""

        config = self._load_config()

        if date not in config:
            return

        config[date] = list(set(config[date]) - set(contact_ids))
        self._save_config(config)

    def is_valid(self, contact_id: str) -> bool:
        """check if the talker is valid

        Args:
            contact_id: talker.contact_id

        Returns:
            bool: the result of the code
        """
        date = datetime.today().strftime('%Y-%m-%d')
        config = self._load_config()
        return contact_id in config.get(date, [])

    async def on_message(self, msg: Message) -> None:
        """handle the authorize"""
        room = msg.room()
        if msg.is_self() or not room:
            return
        if not await msg.mention_self():
            return

        mention_list = await msg.mention_list()
        if len(mention_list) <= 1:
            return

        clear_text = remove_at_info(msg.text()).strip()
        if not clear_text:
            await msg.say('如果您想授权此群友，请添加文字内容：今日授权、明日授权等关键字')
            return

        if clear_text == '今日授权':
            date = datetime.today()
        elif clear_text == '明日授权':
            date = datetime.today() + timedelta(days=1)
        else:
            await msg.say(f'如果您想授权此群友，请添加文字内容：今日授权、明日授权等关键\n{clear_text}为无效关键字')

        date_string = date.strftime('%Y-%m-%d')
        self.authorize(date_string, [contact.contact_id + room.room_id for contact in mention_list])
