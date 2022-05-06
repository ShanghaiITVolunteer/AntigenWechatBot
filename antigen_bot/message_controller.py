from __future__ import annotations
from typing import Dict, List, Optional, Union
import functools
from copy import deepcopy

from wechaty import Message, Wechaty, WechatyPlugin


class MessageController:
    """Store the Message Id Container"""
    _instance: Optional[MessageController] = None
    def __init__(self) -> None:
        self.ids = set()
        self.plugin_names: List[str] = []
        
        self.disabled_plugins: Dict[str, List[str]] = {}
    
    def exist(self, message_id: str) -> bool:
        """exist if the message has been emitted

        Args:
            message_id (str): the identifier of message

        Returns:
            bool: if the message is the first message
        """
        if message_id in self.ids:
            return True
        self.ids.add(message_id)
        return False
    
    @classmethod
    def instance(cls) -> MessageController:
        """singleton pattern for MessageIdContainer"""
        if cls._instance is None:
            cls._instance = MessageController()
        return cls._instance

    def init_plugins(self, wechaty: Wechaty) -> None:
        """init the plugins and control the message receiving"""
        if self.plugin_names:
            return
        plugin_map: Dict[str, WechatyPlugin] = wechaty._plugin_manager._plugins
        self.plugin_names = list(plugin_map.keys())
    
    def disable_all_plugins(self, msg: Union[Message, str]) -> None:
        """disable all plugins"""
        if isinstance(msg, Message):
            msg = msg.message_id
        self.disabled_plugins[msg] = deepcopy(self.plugin_names)
    
    def may_disable_message(self, func):
        """decorator for disable the message"""
        @functools.wraps(func)
        async def wrapper(plugin: WechatyPlugin, msg: Message):
            if msg.message_id in self.disabled_plugins and plugin.name in self.disabled_plugins[msg.message_id]:
                return
            await func(plugin, msg)
        return wrapper
