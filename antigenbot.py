import asyncio
# import paddlehub as hub
import json
import os
import random

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
)

administrators = ['wxid_a6xxa7n11u5j22']  #管理员名单，项目运营团队
users = []                                #users = 居委会用户
user_send_quns = {}                            #users对应的群
verify_codes = []

#各种固定文本都维护在这里，可以单独编辑
with open('pre_words.json', encoding='utf-8') as f:
    pre_words = json.load(f)

#module = hub.Module(name="simnet_bow")


async def on_message(msg: Message):
    """
    Message Handler for the Bot
    """

    if msg.is_self() or msg.type() == MessageType.MESSAGE_TYPE_UNSPECIFIED:
        return

    talker = msg.talker()
    #room = msg.room()

    #管理员对话发验证码（一次有效）
    if talker.contact_id in administrators:
        if msg.type() == MessageType.MESSAGE_TYPE_TEXT:
            verify_codes.append(msg.text())
        return

    if talker.contact_id in users:
        if msg.type() in [MessageType.MESSAGE_TYPE_IMAGE, MessageType.MESSAGE_TYPE_VIDEO,
                          MessageType.MESSAGE_TYPE_ATTACHMENT]:
            file_box_buffer = await msg.to_file_box()
            random.shuffle(user_send_quns[talker.contact_id])
            for room in user_send_quns[talker.contact_id]:
                try:
                    await room.say(file_box_buffer)
                except Exception as e:
                    print(e)

        if msg.type() == MessageType.MESSAGE_TYPE_MINI_PROGRAM:
            minipro = await msg.to_mini_program()
            random.shuffle(user_send_quns[talker.contact_id])
            for room in user_send_quns[talker.contact_id]:
                try:
                    await room.say(minipro)
                except Exception as e:
                    print(e)

        if msg.type() == MessageType.MESSAGE_TYPE_URL:
            urlfile = await msg.to_url_link()
            random.shuffle(user_send_quns[talker.contact_id])
            for room in user_send_quns[talker.contact_id]:
                try:
                    await room.say(urlfile)
                except Exception as e:
                    print(e)

        if msg.type() == MessageType.MESSAGE_TYPE_TEXT:
            random.shuffle(user_send_quns[talker.contact_id])
            for room in user_send_quns[talker.contact_id]:
                try:
                    await msg.forward(room)
                except Exception as e:
                    print(e)

        await msg.say(pre_words['no_support_type'])
        return


async def on_login(user: Contact):
    """
    Login Handler for the Bot
    """
    print(user)


async def on_room_invite(room_invitation: RoomInvitation):
    try:
        room_name = await room_invitation.topic()
        inviter = await room_invitation.inviter()
        if inviter.contact_id in users:
            await room_invitation.accept()
            print(f"收到来自{inviter.name}的群聊:{room_name} 邀请,已经自动接受")
            rooms = await xiaoyan.Room.find_all(room_name)
            if rooms:
                for room in rooms:
                    if room.room_id not in user_send_quns[inviter.contact_id]:
                        user_send_quns[inviter.contact_id].append(room.room_id)
                        await room.say(pre_words["hello_qun"])
            else:
                await inviter.say(pre_words['failed_add_qun'])
    except Exception as e:
        print(e)


async def on_room_join(room: Room, invitees: [Contact], inviter: Contact, date):
    mentionlist = [contact.contact_id for contact in invitees]
    await room.say(pre_words["welcome"], mentionlist)
    path = os.getcwd() + '\media\welcome.jpeg'
    filebox = FileBox.from_file(path)
    await room.say(filebox)
    # 检查群成员是否已经将群昵称设为"楼号-门牌号"，如未则提醒，如有则按此更新微信备注（取代昵称）
    for contact in invitees:
        alias = await room.alias(contact)
        if alias:
            if alias != await contact.alias():
                try:
                    await contact.alias(alias)
                    print(f"更新{contact.name}的备注成功!")
                except Exception:
                    print(f"更新{contact.name}的备注失败~")
        else:
            await room.say(pre_words['alias_reminder'], [contact.contact_id])


async def on_friendship(friendship: Friendship):
    print(f'receive friendship<{friendship}> event')

    if friendship.type() == FriendshipType.FRIENDSHIP_TYPE_RECEIVE:
        text = friendship.hello()
        contact = friendship.contact()

        if text in verify_codes:
            await friendship.accept()
            verify_codes.remove(text)
        else:
            await contact.say(pre_words['wrong_verify_code'])


async def on_room_topic(room: Room, new_topic: str, old_topic: str, changer: Contact, date):
    print(f'receive room topic changed event <from<{new_topic}> to <{old_topic}>> from room<{room}> ')
    if changer == xiaoyan.user_self():
        return
    owner = await room.owner()
    if changer != owner:
        await changer.say(pre_words['no_change'])
        await room.topic(old_topic)


async def main():
    """
    Async Main Entry
    """
    if 'WECHATY_PUPPET_SERVICE_TOKEN' not in os.environ:
        print('''
            Error: WECHATY_PUPPET_SERVICE_TOKEN is not found in the environment variables
            You need a TOKEN to run the Python Wechaty. Please goto our README for details
            https://github.com/wechaty/python-wechaty-getting-started/#wechaty_puppet_service_token
        ''')
    global xiaoyan
    xiaoyan = Wechaty()

    # bot.on('scan',      on_scan)
    xiaoyan.on('login', on_login)
    xiaoyan.on('message', on_message)
    xiaoyan.on('room-invite', on_room_invite)
    xiaoyan.on('friendship', on_friendship)
    xiaoyan.on('room-join', on_room_join)
    xiaoyan.on('room-topic', on_room_topic)

    await xiaoyan.start()

    print('[Python Wechaty] xiaoyan Bot started to serve the people')


asyncio.run(main())

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
