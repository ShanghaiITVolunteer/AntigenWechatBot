"""
AntigenWechatBot(a xiaoyan-bot) - https://github.com/ShanghaiITVolunteer/AntigenWechatBot 
Author: ShanghaiITVolunteer <https://github.com/ShanghaiITVolunteer>
        
Python Wechaty - https://github.com/wechaty/python-wechaty
Authors:    Huan LI (李卓桓) <https://github.com/huan>
            Jingjing WU (吴京京) <https://github.com/wj-Mcat>

puppet-padlocal - https://github.com/wechaty/puppet-padlocal
Authors:    Huan LI (李卓桓) <https://github.com/huan>
            padlocal <https://github.com/padlocal>
            wyh <https://github.com/wyh>
            suhli <https://github.com/suhli>

2022 @ Copyright team Contributors 
Licensed under the Apache License, Version 2.0 (the 'License');
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an 'AS IS' BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
from typing import Optional, List
from datetime import datetime

from wechaty import (
    Contact,
    Message,
    Wechaty,
    MessageType,
    FileBox,
    Room,
    RoomInvitation,
    Friendship,
    FriendshipType,
    WechatyOptions,

)
from wechaty_puppet import get_logger


logger = get_logger('AntigenBot', 'bot.log')


class AntigenBot(Wechaty):
    """AntigenWechatBot is a wechat bot that aims enpowering the primary-level government workers. 
    It is designed during the pandemic in Shanghai, and contains different functions that can 
    automate basic jobs of the primary-level government workers, for example, antigen information collection,
    pandemic information delivery and group purchase announcement.

    AntigenWechatBot是一个用于为基层干（居委会干部）赋能的微信机器人。我们在上海疫情期间开始开发这款软件。它包含但不限于以下功能：抗原数据采集，疫情信息分发和团购信息宣传。
    """
    def __init__(self, options: Optional[WechatyOptions] = None):
        super().__init__(options)
    
        self.administrators = ['wxid_a6xxa7n11u5j22']  #管理员名单，项目运营团队
        self.users = []                                #users = 居委会用户
        self.user_send_quns = {}                            #users对应的群
        self.verify_codes = []

        #各种固定文本都维护在这里，可以单独编辑
        with open('pre_words.json', encoding='utf-8') as f:
            self.pre_words = json.load(f)
    
    async def on_message(self, msg: Message) -> None:
        """
        Message Handler for the Bot
        """

        if msg.is_self() or msg.type() == MessageType.MESSAGE_TYPE_UNSPECIFIED:
            return

        talker = msg.talker()
        #room = msg.room()

        #管理员以文本形式向bot发验证码（一次有效），用户只有凭验证码才能成功添加bot好友，且验证码仅一次有效
        if talker.contact_id in self.administrators:
            if msg.type() == MessageType.MESSAGE_TYPE_TEXT:
                self.verify_codes.append(msg.text())
            return

        #判断是否在users列表里面，如果在的话，把user的信息以"乱序"转发到users所属的群里
        if talker.contact_id in self.users:
            if msg.type() in [MessageType.MESSAGE_TYPE_IMAGE, MessageType.MESSAGE_TYPE_VIDEO,
                            MessageType.MESSAGE_TYPE_ATTACHMENT]:
                file_box_buffer = await msg.to_file_box()
                random.shuffle(self.user_send_quns[talker.contact_id])
                for room in self.user_send_quns[talker.contact_id]:
                    try:
                        await room.say(file_box_buffer)
                    except Exception as e:
                        print(e)

            if msg.type() == MessageType.MESSAGE_TYPE_MINI_PROGRAM:
                minipro = await msg.to_mini_program()
                random.shuffle(self.user_send_quns[talker.contact_id])
                for room in self.user_send_quns[talker.contact_id]:
                    try:
                        await room.say(minipro)
                    except Exception as e:
                        print(e)

            if msg.type() == MessageType.MESSAGE_TYPE_URL:
                urlfile = await msg.to_url_link()
                random.shuffle(self.user_send_quns[talker.contact_id])
                for room in self.user_send_quns[talker.contact_id]:
                    try:
                        await room.say(urlfile)
                    except Exception as e:
                        print(e)

            if msg.type() == MessageType.MESSAGE_TYPE_TEXT:
                random.shuffle(self.user_send_quns[talker.contact_id])
                for room in self.user_send_quns[talker.contact_id]:
                    try:
                        await msg.forward(room)
                    except Exception as e:
                        print(e)

            await msg.say(self.pre_words['no_support_type'])
            return

    async def on_room_invite(self, room_invitation: RoomInvitation) -> None:
        """handle something when someone be invited into the room

        功能描述：
            收到入群邀请的处理
            判断user是否在列表里，在的话，自动接受入群邀请，同时把这个群关联到user
            否则的话告知user联系管理员

        Args:
            room_invitation (RoomInvitation): the Room Invitation object which can access the invitation related things 
        """
        room_name = await room_invitation.topic()
        inviter = await room_invitation.inviter()
        if inviter.contact_id in self.users:
            await room_invitation.accept()
            print(f"收到来自{inviter.name}的群聊:{room_name} 邀请,已经自动接受")
            rooms = await self.Room.find_all(room_name)
            if rooms:
                for room in rooms:
                    if room.room_id not in self.user_send_quns[inviter.contact_id]:
                        self.user_send_quns[inviter.contact_id].append(room.room_id)
                        await room.say(self.pre_words["hello_qun"])
            else:
                await inviter.say(self.pre_words['failed_add_qun'])
        else:
            await inviter.say(self.pre_words['not_user'])

    async def on_room_join(self, room: Room, invitees: List[Contact], inviter: Contact, date: datetime) -> None:
        """handle the event when someone enter the room

        功能描述：
            1. 有人新入群后的操作
            2. 主要是欢迎并提醒ta把群昵称换为楼栋-门牌号

        Args:
            room (Room): the Room object
            invitees (List[Contact]): contacts who are invited into toom
            inviter (Contact): inviter
            date (datetime): the time be invited
        """

        mentionlist = [contact.contact_id for contact in invitees]
        await room.say(self.pre_words["welcome"], mentionlist)
        path = os.getcwd() + '\media\welcome.jpeg'
        filebox = FileBox.from_file(path)
        await room.say(filebox)
        # 检查群成员是否已经将群昵称设为"楼号-门牌号"，如未则提醒，如有则按此更新微信备注（取代昵称）
        for contact in invitees:
            if contact == self.user_self():
                continue
            alias = await room.alias(contact)
            if alias:
                if alias != await contact.alias():
                    try:
                        await contact.alias(alias)
                        print(f"更新{contact.name}的备注成功!")
                    except Exception:
                        print(f"更新{contact.name}的备注失败~")
            else:
                await room.say(self.pre_words['alias_reminder'], [contact.contact_id])
    
    async def on_friendship(self, friendship: Friendship) -> None:
        """handle the event when there is friendship changed

        功能描述：

            1. 收到好友邀请的处理
            2. 判断验证信息是否为管理员发放的有效code，有的话接受邀请并失效该code

        Args:
            friendship (Friendship): 
        """
        print(f'receive friendship<{friendship}> event')

        if friendship.type() == FriendshipType.FRIENDSHIP_TYPE_RECEIVE:
            text = friendship.hello()
            contact = friendship.contact()

            if text in self.verify_codes:
                await friendship.accept()
                self.verify_codes.remove(text)
            else:
                await contact.say(self.pre_words['wrong_verify_code'])
    
    async def on_room_topic(self, room: Room, new_topic: str, old_topic: str, changer: Contact, date: datetime) -> None:
        """on room topic changed, 

        功能点：
            1. 群名称被更改后的操作
            2. 如果不是群主改的群名，机器人自动修改回原群名并提醒用户不当操作

        Args:
            room (Room): _description_
            new_topic (str): _description_
            old_topic (str): _description_
            changer (Contact): _description_
            date (datetime): _description_
        """
        print(f'receive room topic changed event <from<{new_topic}> to <{old_topic}>> from room<{room}> ')
        if changer == self.user_self():
            return
        owner = await room.owner()
        if changer.contact_id != owner.contact_id:
            await changer.say(self.pre_words['no_change'])
            await room.topic(old_topic)