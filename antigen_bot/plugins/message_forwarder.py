import json
import os
import re
from typing import (
    Any, Dict, Optional, List
)
from logging import INFO
from wechaty import (
    WechatyPlugin,
    Room,
    Message,
    WechatyPluginOptions
)
from wechaty_puppet import get_logger
from wechaty_plugin_contrib.finders.room_finder import RoomFinder


class MessageForwarderPlugin(WechatyPlugin):
    """
    功能点：
        1. 当被邀请入群，则立马同意，同时保存其相关信息。
        2. 如果是私聊的消息，则直接转发给该用户邀请机器人进入的所有群聊当中
    """
    def __init__(self, options: Optional[WechatyPluginOptions] = None, config_file: str = '.wechaty/message_forwarder.json'):
        super().__init__(options)
        # 1. init the config file
        self.config_file = config_file

        # 2. save the log info into <plugin_name>.log file
        log_file = os.path.join('.wechaty', self.name + '.log')
        self.logger = get_logger(self.name, log_file)

    def _load_message_forwarder_configuration(self) -> Dict[str, Any]:
        """load the message forwarder configuration

        Returns:
            Dict[str, Any]: the message forwarder configuration
        """
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        if not os.path.exists(self.config_file):
            self.logger.error('configuration file not found: %s', self.config_file)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)
            return {}
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    def get_room_finder(self) -> Optional[RoomFinder]:
        """get_room_finder with dynamic style

        Returns:
            RoomFinder: the instance of RoomFinder
        """
        # 1. init the room finder
        config = self._load_message_forwarder_configuration()

        options = []
        if config.get('room_regex', []):
            for regex in config['room_regex']:
                options.append(re.compile(regex))
        
        if config.get('room_ids', []):
            for room_id in config['room_ids']:
                options.append(room_id)
        if options:
            return RoomFinder(options)
        return None
    
    def get_admin_ids(self) -> List[str]:
        """get the admin ids

        Returns:
            List[str]: the admin ids
        """
        config = self._load_message_forwarder_configuration()
        return config.get('admin_ids', [])

    async def on_message(self, msg: Message) -> None:
        talker = msg.talker()
        room = msg.room()
        # 1. 判断是否是私聊信息
        if room:
            return

        if msg.text() == 'ding':
            await talker.say('dong')
            return

        # 2. 判断是否是自己发送的消息
        if talker.contact_id == self.bot.user_self().contact_id:
            return

        # 3. 检查RoomFinder是否存在
        room_finder = self.get_room_finder()

        if room_finder is None:
            return

        # 4. 检查消息发送者是否是居委会成员
        admin_ids = self.get_admin_ids()
        if not admin_ids or talker.contact_id not in admin_ids:
            return

        self.logger.info('=================start to forward message=================')
        await talker.ready()
        self.logger.info('message: %s', msg)

        rooms: List[Room] = await room_finder.match(self.bot)
        for room in rooms:
            self.logger.info('forward to room: %s', room)
            await msg.forward(room)