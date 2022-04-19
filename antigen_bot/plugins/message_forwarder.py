import asyncio
import json
import os
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


class MessageForwarderPlugin(WechatyPlugin):
    """
    功能点：
        1. 当被邀请入群，则立马同意，同时保存其相关信息。
        2. 如果是私聊的消息，则直接转发给该用户邀请机器人进入的所有群聊当中

    Args:
        WechatyPlugin (_type_): _description_
    """
    def __init__(self, options: Optional[WechatyPluginOptions] = None):
        super().__init__(options)

        self._data_file = 'message_forwarder.json'
        self.user2rooms: Dict[str, List[str]] = self._read_data()

    def _read_data(self, ):
        if not os.path.exists(self._data_file):
            return defaultdict(list)
        
        try:
            with open(self._data_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            data = defaultdict(list)
        return data
    
    def _add_user_room(self, user: Contact, room_id: str) -> None:
        self.user2rooms[user.contact_id].append(room_id)

        with open(self._data_file, 'w') as f:
            json.dump(self.user2rooms, f, ensure_ascii=False)
    
    async def on_message(self, msg: Message) -> None:
        talker = msg.talker()
        room = msg.room()
        # 1. 判断是否是私聊信息
        if room:
            return

        # 2. 判断是否是自己发送的消息
        if talker.contact_id == self.bot.user_self().contact_id:
            return

        # 3. 检查消息发送者是否是居委会成员
        if talker.contact_id not in self.user2rooms:
            return
        
        # 4. 检查该用户是否有邀请入群
        room_topics: List[str] = self.user2rooms.get(talker.contact_id, [])
        for room_topic in room_topics:
            room = await self.bot.Room.find(room_topic)
            if not room:
                continue

            await msg.forward(room)

    # async def on_room_topic(self, room: Room, new_topic: str, old_topic: str, changer: Contact, date: datetime) -> None:
    #     return await super().on_room_topic(room, new_topic, old_topic, changer, date)

    # async def on_room_invite(self, room_invitation: RoomInvitation) -> None:
    #     """理论上，只要是添加上好友的人，就可以进行直接被拉入各种群，因为已经做了身份验证

    #     Args:
    #         room_invitation (RoomInvitation): the object of room Invitation
    #     """
    #     print("触发群邀请")
    #     inviter = await room_invitation.inviter()
    #     await inviter.ready()

    #     # TODO: use the temp api to check friend
    #     if inviter.payload.friend:
    #         await room_invitation.accept()

    #         # sleep to sync the room info
    #         await asyncio.sleep(60)

    #         topic = await room_invitation.topic()
    #         room = await self.bot.Room.find(topic)
    #         if room:
    #             self._add_user_room(inviter, topic)

    # async def on_room_join(self, room: Room, invitees: List[Contact], inviter: Contact, date: datetime) -> None:
    #     bot_self = self.bot.user_self()
    #     is_self_invited_to_room = any([contact.contact_id == bot_self.contact_id for contact in invitees])

    #     if is_self_invited_to_room:
    #         self._add_user_room(inviter, room.room_id)
