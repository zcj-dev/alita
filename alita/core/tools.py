"""工具系统：定义工具结构 + 注册表。

每个工具 = 名字 + 一段给模型看的说明 + 一个真实可调用的 Python 函数。

这里是「Action 行动模块」的地基：
后续联网、读文件、读写记忆、调用外部 API……全都往这个注册表里加。
"""
from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str          # 唯一名字，模型调用时用
    description: str   # 给模型看的说明：干什么、参数怎么写
    func: Callable     # 真实执行的 Python 函数，入参为字符串


class ToolRegistry:
    """工具注册表：注册、查询、调用、生成给模型的工具清单。"""

    def __init__(self):
        self._tools = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool
        return tool

    def get(self, name):
        return self._tools.get(name)

    def call(self, name, arg):
        """调用工具，统一异常处理——工具出错不能让整个循环崩掉。"""
        tool = self._tools.get(name)
        if tool is None:
            return f"错误：没有名为 {name} 的工具"
        try:
            return str(tool.func(arg))
        except Exception as e:
            return f"工具执行出错：{e}"

    def format_prompt(self):
        """生成注入到 system prompt 里的工具清单文本。"""
        lines = []
        for tool in self._tools.values():
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)
