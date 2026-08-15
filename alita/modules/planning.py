"""Planning 规划模块 —— 让 MONENG 面对复杂任务先列计划再动手。

四大模块里的第三个。核心能力：
- 任务拆解（Plan）：把复杂任务拆成 3-6 个可执行步骤
- 反思（Reflexion）：执行后评估结果，不足就给出改进意见

配合 MONENGAgent.solve() 使用，形成 Plan-and-Execute + Reflexion 进阶循环。
"""
import re

from alita.core.llm import LLMClient


class Planner:
    """规划器：拆解任务 + 反思结果。"""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def make_plan(self, task):
        """把任务拆成步骤列表，返回 list[str]。"""
        prompt = (
            "请把下面的任务拆解成 3-6 个清晰的执行步骤。\n"
            "只输出步骤列表，每行一个，格式「1. 步骤内容」，不要输出其他任何内容。\n\n"
            f"任务：{task}\n"
        )
        reply = self.llm.chat([{"role": "user", "content": prompt}])
        return self._parse_steps(reply)

    def critique(self, task, result):
        """Reflexion：评估结果是否够好，返回「通过」或「改进意见：...」。"""
        prompt = (
            "请评估下面这个任务执行结果是否已经完整、正确、可直接交付。\n"
            "如果结果已经足够好，只回复两个字：通过\n"
            "否则回复「改进意见：」后面写清楚哪里不足、怎么改。\n\n"
            f"任务：{task}\n"
            f"执行结果：{result}\n"
        )
        return self.llm.chat([{"role": "user", "content": prompt}]).strip()

    @staticmethod
    def _parse_steps(text):
        """从模型输出里提取步骤列表，容错处理格式不规范的输出。"""
        steps = re.findall(r"^\s*\d+[.、）)]\s*(.+)$", text, re.MULTILINE)
        if steps:
            return [s.strip() for s in steps]
        return [line.lstrip("-•* ").strip() for line in text.splitlines() if line.strip()]
