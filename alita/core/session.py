"""会话管理：维护多轮对话历史。

骨架阶段的关键一环：让 ALITA 从「一问一答」变成「能记得刚才聊了什么」。

重要：这里只存「干净」的对话（用户的话 + 最终回答），
ReAct 中间的 Thought/Action/Observation 是临时草稿，不进会话，
这样记忆里永远是清爽的聊天记录。
"""
from alita.config import Config


class Session:
    """一条对话线：system 提示 + 用户/助手往返历史，带长度裁剪。"""

    def __init__(self, system_prompt="", max_history=None):
        self.max_history = max_history or Config.MAX_HISTORY
        self.messages = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})
        self._trim()

    def get(self):
        """返回当前消息列表的副本。"""
        return list(self.messages)

    def set_system(self, content):
        """更新 system 提示（记忆变化时用），其余消息不动。"""
        self.messages = [m for m in self.messages if m["role"] != "system"]
        self.messages.insert(0, {"role": "system", "content": content})

    def clear(self):
        """清空历史，但保留 system 提示。"""
        self.messages = [m for m in self.messages if m["role"] == "system"]

    def _trim(self):
        """超过上限时，裁掉最旧的非 system 消息（防止上下文无限膨胀）。"""
        non_system = [m for m in self.messages if m["role"] != "system"]
        overflow = len(non_system) - self.max_history
        if overflow <= 0:
            return

        removed = 0
        kept = []
        for m in self.messages:
            if m["role"] != "system" and removed < overflow:
                removed += 1
            else:
                kept.append(m)
        self.messages = kept
