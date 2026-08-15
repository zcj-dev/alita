"""ReAct 智能体循环 —— MONENG 的「发动机」。

ReAct = Reasoning(推理) + Acting(行动)。
每一轮：Thought(想) → Action(做) → Observation(看结果)，循环直到给出 Final Answer。

这个循环是四大模块的挂载点：模块通过「往 system prompt 注入一段内容」来扩展它。
- Profile  画像：注入「人设段」（persona）
- Memory   记忆：注入「记忆段」（memory）
- Planning 规划：注入「计划段」
- Action   行动：扩展 ToolRegistry
"""
import logging
import re

from alita.config import Config
from alita.core.llm import LLMClient
from alita.core.tools import ToolRegistry

logger = logging.getLogger("alita.react")


# persona / memory 占位符由 MONENGAgent 用各模块的 render() 填进去
SYSTEM_TEMPLATE = """{persona}

{memory}

## 你的能力

你会用 ReAct 模式解决问题：先思考，需要外部信息时调用工具查证，再给出回答。

每一轮严格按下面格式输出（Thought 之后，Action 和 Final Answer 二选一）：

Thought: 我这一步该怎么想
Action: 工具名[参数]

当获得足够信息后，输出：
Thought: 我已经能回答了
Final Answer: 给用户的完整回答

## 可用工具

{tools}

规则：
1. 一次只调用一个工具；
2. 需要外部信息（计算、时间、天气、文件、搜索等）时，先用工具查，不要瞎猜；
3. 用中文回答用户。"""


class ReActAgent:
    """无状态 ReAct 循环引擎：不自己记对话，只在传入的消息上跑一轮循环。

    之所以「无状态」，是为了把「推理」和「记忆」解耦——
    记忆交给 Session 和 MemoryModule，这里专心把循环跑对。
    """

    def __init__(self, llm: LLMClient, tools: ToolRegistry):
        self.llm = llm
        self.tools = tools

    def build_system_prompt(self, persona="", memory=""):
        """组装完整 system prompt = 人设段 + 记忆段 + 能力段 + 工具清单。"""
        return SYSTEM_TEMPLATE.format(
            persona=persona, memory=memory, tools=self.tools.format_prompt()
        )

    def ask(self, question, persona="", memory="", verbose=True):
        """便捷方法：单问（不带历史），内部拼好 system + user 再跑循环。"""
        messages = [
            {"role": "system", "content": self.build_system_prompt(persona, memory)},
            {"role": "user", "content": question},
        ]
        return self.run(messages, verbose=verbose)

    def run(self, messages, verbose=True):
        """在给定消息（可含多轮历史）上执行一次完整 ReAct，返回最终回答。

        messages 的最后一条应是用户问题；内部会 copy，不污染原列表。
        """
        working = list(messages)  # 草稿本：只在这里追加中间过程

        for step in range(1, Config.MAX_STEPS + 1):
            reply = self.llm.chat(working)
            logger.info("第 %d 轮模型输出：%s", step, reply.replace("\n", " | "))

            if verbose:
                print(f"\n--- 第 {step} 轮 ---")
                print(reply)

            # 1) 已经给出最终回答，直接收尾
            if "Final Answer:" in reply:
                return self._extract_final(reply)

            # 2) 解析 Action 并执行工具
            action = self._extract_action(reply)
            if action is None:
                # 既没有 Final Answer 也没有 Action：引导模型继续
                working.append({"role": "assistant", "content": reply})
                working.append({
                    "role": "user",
                    "content": "请继续：如果能回答了就输出 Final Answer；否则输出 Action 调用工具。",
                })
                continue

            tool_name, arg = action
            observation = self.tools.call(tool_name, arg)
            logger.info("第 %d 轮工具 %s[%s] => %s", step, tool_name, arg,
                        observation.replace("\n", " | "))

            if verbose:
                print(f"Observation: {observation}")

            # 把这一轮的「思考+行动」和「观察结果」一起喂回给模型
            working.append({"role": "assistant", "content": reply})
            working.append({"role": "user", "content": f"Observation: {observation}"})

        return "（达到最大步数仍未完成，请尝试简化问题或增加 MAX_STEPS）"

    @staticmethod
    def _extract_action(text):
        """从模型输出里解析 `Action: 工具名[参数]`。"""
        m = re.search(r"Action:\s*([a-zA-Z_]+)\s*\[(.*?)\]", text, re.DOTALL)
        if not m:
            return None
        return m.group(1), m.group(2).strip()

    @staticmethod
    def _extract_final(text):
        """从模型输出里截取 Final Answer 之后的内容。"""
        return text.split("Final Answer:", 1)[-1].strip()
