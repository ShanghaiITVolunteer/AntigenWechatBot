import json
import os
import re
import time
from typing import (
    Dict, Optional, Any
)
from wechaty import (
    FileBox,
    MessageType,
    WechatyPlugin,
    Message,
    WechatyPluginOptions
)
from wechaty_puppet import get_logger
from datetime import datetime


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

        #self.dynamic_plugin = dynamic_plugin

        self.data = self._load_message_forwarder_configuration()
        self.listen_to_forward = {}   #记录转发状态
        self.last_loop = {}    #记录上一轮发送群名

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
        date = datetime.today().strftime('%Y-%m-%d')
        for id in data.keys():
            if "auth" not in data[id].keys():
                data[id]["auth"] = {date: []}
        return data

    async def forward_message(self, id, msg: Message, regex):
        """forward the message to the target conversations

        Args:
            msg (Message): the message to forward
            regex (the compile object): the conversation filter
        """
        rooms = await self.bot.Room.find_all()

        self.last_loop[id] = []

        if msg.type() in [MessageType.MESSAGE_TYPE_IMAGE, MessageType.MESSAGE_TYPE_VIDEO, MessageType.MESSAGE_TYPE_ATTACHMENT]:
            file_box = await msg.to_file_box()
            file_path = '.wechaty/' + file_box.name
            await file_box.to_file(file_path, overwrite=True)
            file_box = FileBox.from_file(file_path)

            for room in rooms:
                await room.ready()
                topic = room.payload.topic
                if regex.search(topic) and file_box:
                    await room.say(file_box)
                    self.last_loop[id].append(topic)

        if msg.type() in [MessageType.MESSAGE_TYPE_TEXT, MessageType.MESSAGE_TYPE_URL, MessageType.MESSAGE_TYPE_MINI_PROGRAM]:
            for room in rooms:
                await room.ready()
                topic = room.payload.topic
                if regex.search(topic):
                    await msg.forward(room)
                    self.last_loop[id].append(topic)

        self.logger.info('=================finish to On_call_Notice=================\n\n')

    async def on_message(self, msg: Message) -> None:
        if msg.is_self() or msg.talker().contact_id == "weixin":
            return

        talker = msg.talker()
        date = datetime.today().strftime('%Y-%m-%d')

        if (talker.contact_id in self.data.keys()) and ("撤销" in msg.text()) and (await msg.mention_self()):
            if msg.room().room_id in self.data[talker.contact_id]["auth"].get(date, []):
                self.data[talker.contact_id]["auth"][date].remove(msg.room().room_id)
                await msg.say("本群转发授权已经撤销，如需转发，请管理人员再次授权")
            else:
                await msg.room().say("本群未开启授权，如需授权，请在被授权群中@我并发送 授权", [talker.contact_id])
            return

        if (talker.contact_id in self.data.keys()) and ("授权" in msg.text()) and (await msg.mention_self()):
            if date in self.data[talker.contact_id]["auth"].keys():
                self.data[talker.contact_id]["auth"][date].append(msg.room().room_id)
            else:
                self.data[talker.contact_id]["auth"][date] = [msg.room().room_id]
            await msg.room().say("本群授权已开启，如需撤销，请在本群中@我并发送 撤销", [talker.contact_id])
            await msg.say("本群已授权开启转发，授权期仅限今日（至凌晨12点）。转发请按如下格式： @我 楼号 内容（均用空格隔开）")
            return

        # 如果是转发状态，那么就直接转发
        if talker.contact_id in self.listen_to_forward.keys():
            #群消息要先鉴权
            if msg.room():
                if self.listen_to_forward[talker.contact_id][2] not in self.data[self.listen_to_forward[talker.contact_id][1]]["auth"].get(date, []):
                    del self.listen_to_forward[talker.contact_id]
                    await msg.say("呵呵，你的权限刚刚被取消了哦~")
                    return

            await self.forward_message(talker.contact_id, msg, self.listen_to_forward[talker.contact_id][0])
            if msg.room():
                if self.last_loop.get(talker.contact_id, []):
                    await msg.room().say("已转发，@我并发送查询，查看转发群记录", [talker.contact_id])
                else:
                    await msg.room().say("呵呵，未找到可通知的群，请重试", [talker.contact_id])
            else:
                if self.last_loop.get(talker.contact_id, []):
                    await msg.say("已转发，@我并发送查询，查看转发群记录")
                else:
                    await msg.say("呵呵，未找到可通知的群，请重试")
            del self.listen_to_forward[talker.contact_id]
            return

        # 3. 判断是否来自工作群或者指定联系人的消息（优先判定群）
        if msg.room():
            if not await msg.mention_self():
                return
            text = await msg.mention_text()
            id = msg.room().room_id
        else:
            text = msg.text()
            id = talker.contact_id

        if text == "查询":
            if self.last_loop.get(talker.contact_id, []):
                for record in self.last_loop[talker.contact_id]:
                    await msg.say(record)
            else:
                await msg.say("未查到对应您的上一轮通知记录")
            return

        token = None
        if id in self.data.keys():
            token = id
        else:
            for key, value in self.data.items():
                if id in value["auth"].get(date, []):
                    token = key
                    break

        if token:
            spec = self.data[token]
        else:
            await msg.say("呵呵，你没有权限哦~")
            return

        words = re.split(r"\s+?", text)

        # 4. 检查msg.text()是否包含关键词
        reply = ""
        file_box = None
        for word in words:
            if word in spec.keys():
                self.logger.info('=================start to On_call_Notice=================')
                await talker.ready()
                self.logger.info('message: %s', msg)

                if "hold" in spec[word].keys():
                    await msg.say("收到，等待{0}秒后，按预设【{1}】进行发送".format(spec[word]["hold"], word))
                    time.sleep(spec[word]["hold"])
                else:
                    await msg.say("收到，现在开始按预设【{}】进行发送".format(word))

                reply = spec[word].get("reply")

                if "media" in spec[word].keys():
                    file_box = FileBox.from_file("media/" + spec[word]["media"])
                words.remove(word)

        if (not reply) and ("转发" not in words):
            return

        # 5. 匹配群进行转发
        pre_fix = self.data[token].get('pre_fix')

        if not pre_fix:
            await msg.say("还未配置所属小区，通知未触发")
            return

        words_more = []
        for word in words:
            if re.search(r"\d+[\-:：~\u2014\u2026\uff5e\u3002]{1,2}\d+", word, re.A):
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
        words = set(filter(None, words))

        regex_words = "|".join(words)
        if len(regex_words) == 0:
            await msg.say("呵呵，未找到可通知的群，请重试")
            return
        regex = re.compile(r"{0}.*\D({1})\D.*".format(pre_fix, regex_words))

        if "转发" in words:
            self.listen_to_forward[talker.contact_id] = [regex, token, id]
            #这一步分别存储 转发规则、授权来源和对话号，后二者用于后续鉴权
            return

        rooms = await self.bot.Room.find_all()

        self.last_loop[talker.contact_id] = []
        for room in rooms:
            await room.ready()
            topic = room.payload.topic
            if regex.search(topic):
                await room.say(reply)
                if file_box:
                    await room.say(file_box)
                self.last_loop[talker.contact_id].append(topic)

        self.logger.info('=================finish to On_call_Notice=================\n\n')

        if msg.room():
            if self.last_loop.get(talker.contact_id, []):
                await msg.room().say("已转发，@我并发送查询，查看转发群记录", [talker.contact_id])
            else:
                await msg.room().say("呵呵，未找到可通知的群，请重试", [talker.contact_id])
        else:
            if self.last_loop.get(talker.contact_id, []):
                await msg.say("已转发，@我并发送查询，查看转发群记录")
            else:
                await msg.say("呵呵，未找到可通知的群，请重试")