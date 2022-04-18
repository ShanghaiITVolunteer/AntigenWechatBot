import json
import os
from typing import (
    Dict, Optional, List
)
from collections import defaultdict
from datetime import datetime

from wechaty import (
    WechatyPlugin,
    Wechaty,
    WechatyPluginOptions,
    RoomInvitation,
    Room,
    Contact
)


class WatchRoomTopicPlugin(WechatyPlugin):
    """WatchRoomTopicPlugin 
    """

    def __init__(self, options: Optional[WechatyPluginOptions] = None):
        super().__init__(options)
        
        self.please_do_not_change_room_topic = "请不要修改群名称，谢谢！"

    async def on_room_topic(self, room: Room, new_topic: str, old_topic: str, changer: Contact, date: datetime) -> None:
        """on room topic changed, 

        功能点：
            1. 群名称被更改后的操作
            2. 如果不是群主改的群名，机器人自动修改回原群名并提醒用户不当操作

        Args:
            room (Room): The Room object 
            new_topic (str): old topic
            old_topic (str): new topic
            changer (Contact): the contact who change the topic
            date (datetime): the time when the topic changed
        """
        print(f'receive room topic changed event <from<{new_topic}> to <{old_topic}>> from room<{room}> ')
        if changer.contact_id == self.bot.user_self().contact_id:
            return
        owner = await room.owner()
        if changer.contact_id != owner.contact_id:
            await changer.say(self.please_do_not_change_room_topic)
            await room.topic(old_topic)