"""basic ding-dong bot for the wechaty plugin"""
import os
from typing import List, Optional

from wechaty import Message, MessageType, Wechaty, WechatyPluginOptions
from wechaty.plugin import WechatyPlugin
from wechaty_puppet import get_logger
import requests

from dataclasses import dataclass, field

from antigen_bot.message_controller import MessageController


@dataclass
class AntigenResponse:
    positive: List[float] = field(default_factory=list)
    negative: List[float] = field(default_factory=list) 


class AntigenImagesPlugin(WechatyPlugin):
    """DingDong Plugin"""
    def __init__(self, options: Optional[WechatyPluginOptions] = None, endpoint: Optional[str] = None):
        super().__init__(options)
        self.cache_dir = os.path.join('.wechaty', self.name)
        os.makedirs(self.cache_dir, exist_ok=True)

        self.logger = get_logger('AntigenImage', file='.wechaty/antigen_images.log')
        self.command = "#test-antigen-images"
        self.admin_status = {}
        self.endpoint = endpoint or os.environ.get('antigen_image_endpoint', None)

    @MessageController.instance().may_disable_message
    async def on_message(self, msg: Message) -> None:
        """listen message event"""
        talker = msg.talker()
        text = msg.text()
        room = msg.room()

        if not self.endpoint:
            return

        if self.command in text:
            MessageController.disable_all_plugins(msg)
            self.admin_status[talker.contact_id] = True
            
            if room:
                await room.say('waiting for your antigen image ...', mention_ids=[talker.contact_id])
            else:
                await talker.say('waiting for your antigen image ...')
            
        if msg.type() in [MessageType.MESSAGE_TYPE_IMAGE, MessageType.MESSAGE_TYPE_ATTACHMENT] and talker.contact_id in self.admin_status:
            MessageController.disable_all_plugins(msg)

            file_box = await msg.to_file_box()
            target_file = os.path.join(self.cache_dir, file_box.name)
            
            await file_box.to_file(target_file, overwrite=True)
            result = requests.post(self.endpoint, files={'antigen': open(target_file, 'rb')}).json()
            
            antigen_response: AntigenResponse = AntigenResponse(**result['data'])

            if not antigen_response.positive and not antigen_response.negative:
                return
            
            res_descriptions = []
            for metric in antigen_response.positive:
                res_descriptions.append(f'阳性：{metric:4f}')
            
            for metric in antigen_response.negative:
                res_descriptions.append(f'阴性：{metric:4f}')

            info = f'\nantigen result: \n===================\n' + '\n'.join(res_descriptions)
            if room:
                await room.say(info, mention_ids=[talker.contact_id])
            else:
                await msg.say(info)
