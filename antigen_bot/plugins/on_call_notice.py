import json
import os
import re
import time
from typing import (
    Any, Dict, Optional,)
from wechaty import (
    FileBox,
    MessageType,
    WechatyPlugin,
    Message,
    WechatyPluginOptions
)
from wechaty_puppet import get_logger


class OnCallNoticePlugin(WechatyPlugin):
    """
    功能点：
        1. 侦测"工作群"中或指定联系人的特定格式消息（key_words和楼号数字的任意组合），进行预设通知内容的触发
        2. 应用于"[团购送达](https://github.com/ShanghaiITVolunteer/AntigenWechatBot/issues/25#issuecomment-1104817261)"、
        "[核酸提醒](https://github.com/ShanghaiITVolunteer/AntigenWechatBot/issues/25#issuecomment-1104823018)"等需求场景
        3. 配置文件：.wechaty/on_call_notice.json(存储keyword已经对应的回复文本（必须）、群聊名称pre_fix(必须）、回复媒体（存贮在media/）以及延迟时间）
    """
    def __init__(self, options: Optional[WechatyPluginOptions] = None, config_file: str = '.wechaty/on_call_notice.json'):
        super().__init__(options)
        # 1. init the config file
        self.config_file = config_file

        # 2. save the log info into <plugin_name>.log file
        log_file = os.path.join('.wechaty', self.name + '.log')
        self.logger = get_logger(self.name, log_file)

        self.last_loop = {}

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

    async def on_message(self, msg: Message) -> None:
        if msg.type() != MessageType.MESSAGE_TYPE_TEXT:
            return
        talker = msg.talker()
        room = msg.room()
        # 1. 判断是否是群聊信息
        if room:
            id = room.room_id
        else:
            id = talker.contact_id

        if msg.text() == 'ding':
            await talker.say('dong')
            return

        # 2. 判断是否是自己发送的消息
        if talker.contact_id == self.bot.user_self().contact_id:
            return

        msg_data = self._load_message_forwarder_configuration()

        # 3. 判断是否来自工作群或者指定联系人的消息（优先判定群）
        if id not in msg_data.keys():
            return

        if msg.text() == "查询":
            if self.last_loop.get(id, []):
                for record in self.last_loop[id]:
                    await msg.say(record)
            else:
                await msg.say("未查到上一轮通知记录")
            return

        words = re.split(r"\s+?", msg.text())

        # 4. 检查msg.text()是否包含关键词
        reply = ""
        file_box = None
        for word in words:
            if word in msg_data[id].keys():
                self.logger.info('=================start to On_call_Notice=================')
                await talker.ready()
                self.logger.info('message: %s', msg)

                if "hold" in msg_data[id][word].keys():
                    await msg.say("收到，等待{0}秒后，按预设【{1}】进行发送".format(msg_data[id][word]["hold"], word))
                    time.sleep(msg_data[id][word]["hold"])
                else:
                    await msg.say("收到，现在开始按预设【{}】进行发送".format(word))

                reply = msg_data[id][word].get("reply")

                if "media" in msg_data[id][word].keys():
                    file_box = FileBox.from_file("media/" + msg_data[id][word]["media"])
                words.remove(word)

        if not reply:
            return

        # 5. 匹配群进行转发
        pre_fix = msg_data[id].get('pre_fix')

        if not pre_fix:
            await msg.say("还为配置所属小区，通知未触发")
            return

        words_more = []
        for word in words:
            if re.search(r"\d+[\-\_:：~\u2014\u2026\uff5e\u3002]{1,2}\d+", word, re.A):
                two_num = re.findall(r"\d+", word, re.A)
                if len(two_num) == 2:
                    try:
                        n, m = int(two_num[0]), int(two_num[1])
                        if n > m:
                            m, n = int(two_num[0]), int(two_num[1])
                        for k in range(n, m):
                            words_more.append(str(k))
                        words_more.append(str(m))
                    except:
                        await msg.say("{0}中所包含的楼栋未成功通知，请按正确指定格式重试".format(word))
                else:
                    await msg.say("{0}中所包含的楼栋未成功通知，请按正确指定格式重试".format(word))

        words.extend(words_more)
        words = filter(None, words)
        regex_words = "|".join(set(words))
        regex = re.compile(r"{0}.*\D({1})\D.*".format(pre_fix, regex_words))

        await room.ready()
        rooms = await self.bot.Room.find_all()

        self.last_loop[id] = []
        for room in rooms:
            topic = await room.topic()
            if regex.search(topic):
                await room.say(reply)
                if file_box:
                    await room.say(file_box)
                self.last_loop[id].append(topic)

        self.logger.info('=================finish to On_call_Notice=================\n\n')

        if self.last_loop[id]:
            await msg.say("通知已完成，对我说：查询，以查看上一轮发送群聊列表")
        else:
            await msg.say("未找到可通知的群，请重试")