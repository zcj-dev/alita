"""MONENG 演示脚本 —— 跑几个典型场景，截图做作品集。

用法：
    python demo.py

前置：已复制 .env.example 为 .env 并填入 LLM_API_KEY。
"""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from alita.agent import MONENGAgent
from alita.config import setup_logging


def run_scene(agent, title, question):
    print("\n" + "=" * 56)
    print(f"  【{title}】")
    print(f"  你：{question}")
    print("=" * 56)
    if question.startswith("plan "):
        return agent.solve(question[5:])
    return agent.chat(question)


def main():
    setup_logging()
    agent = MONENGAgent()

    scenes = [
        ("场景1 · 长期记忆", "我叫小张，喜欢喝咖啡，正在学 Python"),
        ("场景2 · 记忆召回", "还记得我叫什么、喜欢喝什么吗？"),
        ("场景3 · 工具调用", "北京现在天气怎么样？顺便算一下 123*456+78"),
        ("场景4 · 规划模式", "plan 帮我做一个北京两日游攻略"),
    ]

    for title, q in scenes:
        answer = run_scene(agent, title, q)
        print(f"\nMONENG：{answer}")

    print("\n" + "=" * 56)
    print("  演示结束。以上输出可直接截图用于作品集。")
    print("=" * 56)


if __name__ == "__main__":
    main()
