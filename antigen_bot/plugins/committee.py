"""Committee Plugin which provide more"""
import os
from uuid import uuid4
from typing import Optional
from logging import Logger

from wechaty import FileBox, Message, MessageType, WechatyPluginOptions
from wechaty.plugin import WechatyPlugin
from wechaty_puppet import get_logger

from group_purchase.community.community_base import CommunityBase
from group_purchase.community.jia_yi_shui_an import JiaYiShuiAn
from group_purchase.purchase_deliver.parser_mng import get_excel_parser
from group_purchase.utils.utils import *

from antigen_bot.forward_config import ConfigFactory


class CommitteePlugin(WechatyPlugin):
    """居委会插件"""
    def __init__(
        self,
        community: Optional[CommunityBase] = None,
        config_file: Optional[str] = None,
        options: Optional[WechatyPluginOptions] = None,
        command: str = '#团购订单',
    ):
        super().__init__(options)

        self.command = command
        self.community = community or JiaYiShuiAn()

        self.log: Logger = get_logger(self.name, f'.wechaty/{self.name}.log')

        self.cache_dir = os.path.join('.wechaty', self.name)

        # check the config file
        if not config_file:
            config_file = os.path.join(self.cache_dir, 'config.xlsx')
            if not os.path.exists(config_file):
                raise ValueError(
                    'the config_file argument is None and there is no default config '
                    f'file<config.json> under cache dir: {self.cache_dir}'
                )
        self.config_file = config_file
        self.config_factory = ConfigFactory(self.config_file)
        self.admin_ids = set()
        self.init_admin_ids()

        self.type_name: Optional[str] = False

        self.type_names = ['快团团', '群接龙']
    
    def init_admin_ids(self):
        """init the admin ids"""
        if self.admin_ids and not self.config_factory.config_changed():
            return
        self.admin_ids = set()
        for config in self.config_factory.instance():
            for admin_id in config.admins.keys():
                self.admin_ids.add(admin_id)
    async def on_message(self, msg: Message) -> None:
        """listen message event"""
        if msg.room():
            return
        
        self.init_admin_ids()
        talker = msg.talker()
        if msg.is_self():
            return

        if talker.contact_id not in self.admin_ids:
           return

        if self.type_name:
            if msg.type() == MessageType.MESSAGE_TYPE_ATTACHMENT:
                file_box = await msg.to_file_box()
                if not file_box.name.endswith('.xlsx'):
                    await talker.say('请上传Excel相关文件')
                    return

                file_path = os.path.join(self.cache_dir, f'{uuid4()}-{file_box.name}')
                await file_box.to_file(file_path, overwrite=True)
                parser = get_excel_parser(self.type_name)(open(file_path, 'rb'))

                file_path, _ = os.path.splitext(file_path)
                pdf_file = f'{file_path}.pdf'
                try:
                    result, errors = parser.parse_for_community(self.community)
                except:
                    await msg.say('Excel文件格式解析错误，情先确保文件的格式，请联系管理员')
                    return
            
                if errors:
                    await msg.say(f'单元格:{",".join(errors)} 数据错误，情检查后再上传')
                    return

                result.print_to_pdf(pdf_file)
                file_box = FileBox.from_file(pdf_file)
                await msg.say(file_box)
                await msg.say(f'{self.type_name} 类型文件已处理完毕')
                self.type_name = None
            elif msg.type() in [MessageType.MESSAGE_TYPE_UNSPECIFIED, MessageType.MESSAGE_TYPE_TEXT]:
                return
            else:
                await msg.say(f'请上传Excel文件，如需再次执行解析服务\n请重新输入命令：{self.command}')

        elif msg.text() in self.type_names:
            self.type_name = msg.text()
            await msg.say('请上传Excel文件')
            return

        self.type_name = False
