import json
import os
import re
import asyncio
from typing import (
    Any, Dict, Optional, List
)
from datetime import datetime
from wechaty import (
    Wechaty,
    Contact,
    FileBox,
    MessageType,
    WechatyPlugin,
    Room,
    Message,
    WechatyPluginOptions
)
from wechaty_puppet import get_logger
from wechaty_plugin_contrib.finders.room_finder import RoomFinder
from antigen_bot.message_controller import MessageController



class ForwardRecord:
    """record the forward info"""
    def __init__(self, msg: Message, talker: Contact, rooms: List[Room], max_interval_second: int = 4) -> None:
        self.room_status = {room.room_id: False for room in rooms}
        self.max_interval_seconds = max_interval_second

        self.last_update_time: datetime = None
        self.source_message = msg
        
        loop = asyncio.get_event_loop()
        loop.create_task(self.monitor())
        self.contact = talker

    async def monitor(self):
        """monitor the sended message by the bot"""
        last_update_time = datetime.now() if not self.last_update_time else self.last_update_time
        expired = (datetime.now() - last_update_time).seconds > self.max_interval_seconds
        if not self.last_update_time or not expired:
            await asyncio.sleep(self.max_interval_seconds)
            await self.monitor()
            return
        
        sended_rooms: List[Room] = [room for room, status in self.room_status.items() if status]
        sended_rooms.sort(key=lambda room: room.payload.topic)

        not_sended_rooms: List[Room] = [room for room, status in self.room_status.items() if not status]
        not_sended_rooms.sort(key=lambda room: room.payload.topic)
        info = [
            f'已发送的群<{len(sended_rooms)}>:',
            '\n'.join([f'{room.payload.topic}' for room in sended_rooms]),
            '==========='
            f'未发送的群<{len(not_sended_rooms)}>:',
            '\n'.join([f'{room.payload.topic}' for room in not_sended_rooms]),
        ]
        await self.contact.say('\n'.join(info))

    
    def update_message(self, msg: Message):
        """update the message"""
        room = msg.room()
        if msg.type() != self.source_message.type() or not room or room.room_id not in self.room_status:
            return

        self.last_update_time = datetime.now()
        self.room_status[room.room_id] = True
    

class MessageForwarderPlugin(WechatyPlugin):
    """
    功能点：
        1. 当被邀请入群，则立马同意，同时保存其相关信息。
        2. 如果是私聊的消息，则直接转发给该用户邀请机器人进入的所有群聊当中
    """
    def __init__(
        self,
        options: Optional[WechatyPluginOptions] = None,
        config_file: str = '.wechaty/message_forwarder.json',
        file_box_interval_seconds: int = 2
    ):
        super().__init__(options)
        # 1. init the configs file
        self.config_file = config_file

        # 2. save the log info into <plugin_name>.log file
        log_file = os.path.join('.wechaty', self.name + '.log')
        self.logger = get_logger(self.name, log_file)
        self.file_box_interval_seconds: int = file_box_interval_seconds

    async def init_plugin(self, wechaty: Wechaty) -> None:
        MessageController.instance().init_plugins(wechaty)
        return await super().init_plugin(wechaty)

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

    @MessageController.instance().may_disable_message
    async def on_message(self, msg: Message) -> None:
        talker = msg.talker()
        room = msg.room()
        # 1. 判断是否是私聊信息
        if room:
            return

        # 2. 判断是否是自己发送的消息
        if talker.contact_id == self.bot.user_self().contact_id:
            self.logger.error('receive self message ....')
            # 更新记录
            return
        
        if msg.text() == 'ding':
            await msg.say('dong - ' + self.name)
            return

        # 3. 检查RoomFinder是否存在
        room_finder = self.get_room_finder()

        if room_finder is None:
            return
    
        # 4. 检查消息发送者是否是居委会成员
        admin_ids = self.get_admin_ids()
        self.logger.info(f'get admin ids: {",".join(admin_ids)}')
        if not admin_ids or talker.contact_id not in admin_ids:
            return

        self.logger.info('=================start to forward message=================')
        await talker.ready()
        self.logger.info('message: %s', msg)

        rooms: List[Room] = await room_finder.match(self.bot)
        if rooms:
            self.logger.info(f'matching rooms<{len(rooms)}>')
            for room in rooms:
                self.logger.info(room)
        else:
            self.logger.info('can not find any rooms ...')
        file_box = None
        if msg.type() == MessageType.MESSAGE_TYPE_IMAGE:
            file_box = await msg.to_file_box()
            file_path = '.wechaty/' + file_box.name
            await file_box.to_file(file_path, overwrite=True)
            file_box = FileBox.from_file(file_path)

        # 启用了此插件，则屏蔽掉所有其它插件
        MessageController.instance().disable_all_plugins(msg)
        
        for room in rooms:
            self.logger.info('forward to room: %s', room)
            if file_box is None:
                await msg.forward(room)
                await asyncio.sleep(1)
            else:
                await room.say(file_box)
                # sleep one second
                await asyncio.sleep(self.file_box_interval_seconds)
        self.logger.info('=================finish to forward message=================\n\n')
