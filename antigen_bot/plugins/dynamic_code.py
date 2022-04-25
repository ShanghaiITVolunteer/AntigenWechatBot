from copy import deepcopy
from datetime import datetime, timedelta
import os
from typing import (
    Optional
)
from quart import Quart, request, jsonify
from random import randint
import pandas as pd

from wechaty import (
    FileBox,
    MessageType,
    WechatyPlugin,
    Room,
    Message,
    WechatyPluginOptions
)
from wechaty_puppet import get_logger
from antigen_bot.plugins.config import DATE_FORMAT


class DynamicCodePlugin(WechatyPlugin):
    """
    功能点：
        1. 当被邀请入群，则立马同意，同时保存其相关信息。
        2. 如果是私聊的消息，则直接转发给该用户邀请机器人进入的所有群聊当中
    """
    def __init__(self, options: Optional[WechatyPluginOptions] = None, code_file: str = '.wechaty/dynamic_code.xlsx', max_length: int=5):
        super().__init__(options)
        # 1. init the configs file
        self.code_file = code_file

        # 2. save the log info into <plugin_name>.log file
        log_file = os.path.join('.wechaty', self.name + '.log')
        self.logger = get_logger(self.name, log_file)
        
        self.max_length = max_length
        self.token = os.environ.get('dynamic_token', None)

    def gen_dynamic_code(self):
        """generate the dynamic code"""
        return randint(
            a=pow(10, self.max_length - 1),
            b=pow(10, self.max_length) - 1
        )
    
    def gen_dynamic_code_file(self, hours: int, count: int):
        """generate the dynamic code file

        Args:
            hours (int): expire hours
            count (int): the numbers of new code
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=hours)

        series = []
        for _ in range(count):
            series.append(dict(
                start_time=start_time.strftime(DATE_FORMAT),
                end_time=end_time.strftime(DATE_FORMAT),
                code=self.gen_dynamic_code(),
            ))
        
        all_series = deepcopy(series)
        # 3. add the data into the code file
        if os.path.exists(self.code_file):
            df = pd.read_excel(self.code_file, sheet_name='code')
            for _, row in df.iterrows():
                start_time, end_time = datetime.strptime(row['start_time'], DATE_FORMAT), datetime.strptime(row['end_time'], DATE_FORMAT)
                if start_time <= datetime.now() <= end_time:
                    all_series.append(dict(row))
 
        pd.DataFrame(all_series).to_excel(self.code_file, sheet_name='code', index=False)
        return series

    def is_valid_code(self, code: int) -> bool:
        """check if the code is valid

        Args:
            code (int): the data of the code

        Returns:
            bool: the result of the code
        """
        if not isinstance(code, int):
            if isinstance(code, str) and code.isdigit():
                code = int(code)
            else:
                return False

        # 1. check if the code is in the code file
        if not os.path.exists(self.code_file):
            return False

        # 2. check if the code is valid
        df = pd.read_excel(self.code_file, sheet_name='code')
        if df.empty:
            return False

        df = df[df['code'] == code]
        if len(df) == 0:
            return False

        data = df.iloc[0]
 
        start_time, end_time = datetime.strptime(data['start_time'], DATE_FORMAT), datetime.strptime(data['end_time'], DATE_FORMAT)
        if start_time <= datetime.now() <= end_time:
            return True
        return False

    async def blueprint(self, app: Quart) -> None:
        """register the dynamic code service"""

        def error(msg: str):
            return jsonify(dict(code=500, msg=msg))

        @app.route('/dynamic_code', methods=['GET'])
        async def gen_dynamic_code():
            """generate the dynamic code"""
            if not self.token:
                return error(msg='no token found in plugin')
            
            token = request.args.get('token', None)
            if not token:
                return error(msg='no token found in request query string')
            if token != self.token:
                return error('invalid token')
            
            # 1. get the hours/count data
            hours: int = int(request.args.get('hours', 1))
            count: int = int(request.args.get('count', 1))

            series = self.gen_dynamic_code_file(hours, count)
            return jsonify(dict(code=200, data=series))
