import asyncio
import json
import os
from uuid import uuid4
from typing import (
    Dict, Optional, List
)
from collections import defaultdict
from datetime import datetime
from pyparsing import srange

from wechaty import (
    WechatyPlugin,
    Wechaty,
    WechatyPluginOptions,
    RoomInvitation,
    Room,
    Contact,
    Message
)
from wechaty_puppet import get_logger
import pandas as pd
from quart import Quart, send_file

page_dir = os.path.join(os.path.dirname(__file__), 'pages')


class InfoDownloaderPlugin(WechatyPlugin):
    """Download all of Contacts/Rooms info as excel file"""

    def __init__(self, options: Optional[WechatyPluginOptions] = None):
        super().__init__(options)

        self.cache_dir = os.path.join('.wechaty', self.name)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.logger = get_logger(self.name, f'{self.cache_dir}/log.log')

    async def get_contacts_infos(self):
        """load all of contact info into csv file format"""
        contacts: List[Contact] = await self.bot.Contact.find_all()
        
        infos = []
        for contact in contacts:
            await contact.ready()
            fields = ['id', 'type', 'name', 'alias', 'friend', 'weixin', 'corporation', 'title', 'description', 'phone']
            info = {}
            for field in fields:
                value = getattr(contact.payload, field) or ''
                info[field] = value
            infos.append(info)
        return infos

    async def get_room_infos(self):
        """load all of room info into csv file format"""
        rooms: List[Room] = await self.bot.Room.find_all()
        
        infos = []
        for room in rooms:
            await room.ready()

            info = {}

            # 1. 初始化群基本信息
            topic = await room.topic()
            topic = topic or room.payload.topic

            info['topic'] = topic
            info['room_id'] = room.room_id

            # 2. 初始化群主信息
            owner = await room.owner()
            info['owner'] = owner.name
            info['owner_id'] = owner.contact_id

            # 3. 初始化群成员信息
            members: List[Contact] = await room.member_list()
            info['member_count'] = len(members)

            infos.append(info)
        
        return infos
    
    async def on_message(self, msg: Message) -> None:
        if msg.room():
            return
        
        if msg.text() == '#log-all-contacts':
            self.logger.info('===========================all contacts===========================')
            contacts = await self.get_contacts_infos()
            for contact in contacts:
                self.logger.info(contact)
            self.logger.info('===========================all contacts===========================')
        elif msg.text() == '#log-all-rooms':
            self.logger.info('===========================all rooms===========================')
            rooms = await self.get_room_infos()
            for room in rooms:
                self.logger.info(room)
            self.logger.info('===========================all rooms===========================')
