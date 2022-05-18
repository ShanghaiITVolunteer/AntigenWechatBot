"""Committee Plugin which provide more"""
import os
from typing import Optional, Set
from logging import Logger

from wechaty import FileBox, Message, MessageType, WechatyPluginOptions
from wechaty.plugin import WechatyPlugin
from wechaty_puppet import get_logger

from group_purchase.community.community_base import CommunityBase
from group_purchase.community.jia_yi_shui_an import JiaYiShuiAn
from group_purchase.purchase_deliver.parser_mng import get_excel_parser
from group_purchase.utils.utils import *

from antigen_bot.forward_config import ConfigFactory
from antigen_bot.message_controller import MessageController


class CommitteePlugin(WechatyPlugin):
    """居委会插件

    体验方式：
    1. 添加AntigenBot小助手为好友
    2. 联系秋客天界测试配置
    
    """
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

        self.cache_dir = os.path.join('.wechaty', self.name)
        self.file_cache_dir = os.path.join(self.cache_dir, 'files')
        os.makedirs(self.file_cache_dir, exist_ok=True)

        self.logger: Logger = get_logger(self.name, f'{self.cache_dir}/log.log')

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
        self._admin_ids = set()

        self.type_name: Optional[str] = False

        self.type_names = ['快团团', '群接龙']
        self.cancel_word = '取消'

    @MessageController.instance().may_disable_message
    async def on_message(self, msg: Message) -> None:
        """listen message event"""
        if msg.room():
            return
        
        talker = msg.talker()
        if msg.is_self():
            return

        if talker.contact_id not in self.config_factory.get_admin_ids():
           return

        # 1. cancel the committee task
        if msg.type() == MessageType.MESSAGE_TYPE_TEXT and msg.text() == self.cancel_word:
            self.type_name = None
            MessageController.disable_all_plugins(msg)
            return

        if self.type_name:
            MessageController.disable_all_plugins(msg)
            if msg.type() == MessageType.MESSAGE_TYPE_ATTACHMENT:
                file_box = await msg.to_file_box()

                self.logger.info(f'contact<{talker}> receive file_box<{file_box.name}> ...')
                if not file_box.name.endswith('.xlsx'):
                    await talker.say('请上传Excel相关文件')
                    return

                file_path = os.path.join(self.file_cache_dir, f'{file_box.name}')
                await file_box.to_file(file_path, overwrite=True)
                parser = get_excel_parser(self.type_name)(open(file_path, 'rb'))

                file_name_path, _ = os.path.splitext(file_path)
                pdf_file = f'{file_name_path}.pdf'
                try:
                    result, errors = parser.parse_for_community(self.community)
                except:
                    await msg.say('Excel文件格式解析错误，情先确保文件的格式，请联系管理员')
                    return
            
                if errors:
                    await msg.say(f'单元格:{",".join(errors)} 数据错误，情检查后再上传')
                    return

                result.print_to_pdf(pdf_file)
                self.logger.success(f"contact<{talker}> success for pdf file<{pdf_file}> ...")

                file_box = FileBox.from_file(pdf_file)
                await msg.say(file_box)
                await msg.say(f'{self.type_name} 类型文件已处理完毕')
                self.type_name = None
                
                # delete the temp file
                os.remove(file_name_path)
                os.remove(pdf_file)
                
            elif msg.type() in [MessageType.MESSAGE_TYPE_UNSPECIFIED]:
                return
            else:
                await msg.say(f'请上传Excel文件以执行命令<{self.type_name}>，如需撤销请输入: {self.cancel_word}\n，稍后您重新输入：{"/".join(self.type_names)}关键字可重新执行命令')
        elif msg.text() in self.type_names:
            self.logger.info(f'contact<{talker}> -> command: [{msg.text()}]')
            MessageController.disable_all_plugins(msg)
            self.type_name = msg.text()
            await msg.say('请上传Excel文件')
            return

        self.type_name = False
