from datetime import datetime
import os
import json
from typing import (
    Optional
)

from wechaty import (
    WechatyPlugin,
    WechatyPluginOptions
)
from wechaty_puppet import get_logger


class DynamicAuthorisePlugin(WechatyPlugin):
    """
    功能点：
        1. 管理员通过同时@bot和要被授权的同群组人员，进行授权（默认授权有效期当天）
        2. 发出转发命令的talker是否在当日授权名单中
        3. 一天之内重复授权，后一次会覆盖前一次
    """
    def __init__(self, options: Optional[WechatyPluginOptions] = None, config_file: str = '.wechaty/dynamic_authorise.json'):
        super().__init__(options)
        # 1. init the configs file
        self.config_file = config_file

        # 2. save the log info into <plugin_name>.log file
        log_file = os.path.join('.wechaty', self.name + '.log')
        self.logger = get_logger(self.name, log_file)

        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        if not os.path.exists(self.config_file):
            self.logger.error('configuration file not found: %s', self.config_file)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)

        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        #self.token = os.environ.get('dynamic_token', None)

    def get_authoriers(self):
        return self.data["authoriers"]
    
    def authorise(self, contact_ids: [str]):

        date = datetime.today().strftime('%Y-%m-%d')
        if date in self.data.keys():
            self.data[date].append(contact_ids)
        else:
            self.data[date] = contact_ids

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False)
        self.logger.info('Authorization:', date, contact_ids)
        return

    def is_valid(self, contact_id: str) -> bool:
        """check if the talker is valid

        Args:
            contact_id: talker.contact_id

        Returns:
            bool: the result of the code
        """
        date = datetime.today().strftime('%Y-%m-%d')
        valunteers = self.data.get(date, [])
        if contact_id in valunteers:
            self.logger.info('Authorization Check True', date, contact_id)
            return True
        else:
            self.logger.info('Authorization Check False', date, contact_id)
            return False