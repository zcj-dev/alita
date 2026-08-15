"""ALITAAgent：有状态的陪伴型智能体（完整版）。

把五样东西组合起来：
- ReActAgent（无状态循环引擎）负责「想-做-看」
- Session（会话）负责「记得刚才聊了什么」（短期记忆）
- Profile（画像）负责「是谁、什么性格」
- MemoryModule（长期记忆）负责「认识你、记得你」
- Planner（规划）负责「复杂任务拆解 + 反思」

对外暴露：
- chat()：多轮闲聊 + 简单任务（ReAct）
- solve()：复杂任务（Plan-and-Execute + Reflexion）
- reset() / set_profile()
"""
from alita.core.agent import ReActAgent
from alita.core.llm import LLMClient
from alita.core.session import Session
from alita.core.tools import ToolRegistry
from alita.modules.memory import MemoryModule
from alita.modules.planning import Planner
from alita.modules.profile import COMPANION, Profile
from alita.tools.builtin import register_builtin_tools


class ALITAAgent:
    def __init__(self, llm=None, tools=None, profile=None, memory=None,
                 planner=None, verbose=True):
        self.llm = llm if llm is not None else LLMClient()
        self.tools = tools if tools is not None else ToolRegistry()
        if tools is None:
            register_builtin_tools(self.tools)  # 开箱即用：默认装上内置工具
        self.profile = profile if profile is not None else COMPANION
        self.memory = memory if memory is not None else MemoryModule()
        self.planner = planner if planner is not None else Planner(self.llm)
        self.verbose = verbose

        # 把记忆读写也注册成工具，模型可以自主决定记什么、回忆什么
        for t in self.memory.make_tools():
            self.tools.register(t)

        self.engine = ReActAgent(self.llm, self.tools)
        self.session = Session(self._build_system_prompt())

    def _build_system_prompt(self):
        """把各模块渲染的段交给引擎组装完整 prompt。"""
        return self.engine.build_system_prompt(
            persona=self.profile.render(),
            memory=self.memory.render(),
        )

    def _run_single(self, user_text):
        """单次 ReAct（带最新 system prompt），但不写入会话历史。

        给 solve() 用：复杂任务的中间执行不该污染闲聊会话。
        """
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_text},
        ]
        return self.engine.run(messages, verbose=self.verbose)

    def chat(self, user_text):
        """多轮对话（ReAct）：存用户话 → 跑 ReAct → 存最终回答。"""
        self.session.set_system(self._build_system_prompt())
        self.session.add("user", user_text)
        answer = self.engine.run(self.session.get(), verbose=self.verbose)
        self.session.add("assistant", answer)
        return answer

    def solve(self, task, reflect_rounds=1):
        """复杂任务（Plan-and-Execute + Reflexion）。

        1. Plan：把任务拆成步骤
        2. Execute：按计划逐步执行（内部走 ReAct）
        3. Reflect：评估结果，不足则反思改进后重试
        """
        # 1. Plan
        plan = self.planner.make_plan(task)
        plan_text = "\n".join(f"{i}. {s}" for i, s in enumerate(plan, 1))
        if self.verbose:
            print(f"\n【计划】\n{plan_text}")

        # 2. Execute
        answer = self._run_single(
            f"任务：{task}\n\n你制定的计划：\n{plan_text}\n\n"
            f"请严格按计划逐步执行，最后给我一份完整、可直接使用的答案。"
        )

        # 3. Reflect + Revise
        for round_no in range(1, reflect_rounds + 1):
            feedback = self.planner.critique(task, answer)
            if self.verbose:
                print(f"\n【反思 {round_no}】{feedback}")
            if "通过" in feedback:
                break
            answer = self._run_single(
                f"任务：{task}\n\n上一轮答案：\n{answer}\n\n"
                f"反思意见：{feedback}\n\n请根据反思意见改进你的答案。"
            )

        return answer

    def reset(self):
        """清空短期记忆（对话历史），长期记忆保留。"""
        self.session.clear()

    def set_profile(self, profile: Profile):
        """运行时换人设：重建会话（system prompt 变了，历史一并清空）。"""
        self.profile = profile
        self.session = Session(self._build_system_prompt())
