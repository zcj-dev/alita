"""ALITA 启动入口：命令行交互式对话。

运行方式：
    python main.py

两种模式：
- 普通输入        → chat()：多轮闲聊 + 简单任务（ReAct）
- plan <任务>     → solve()：复杂任务（Plan-and-Execute + Reflexion）
"""
import sys

# Windows 控制台默认 GBK，这里统一输出 UTF-8，避免中文乱码
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from alita.agent import ALITAAgent
from alita.config import Config, setup_logging
from alita.modules.profile import COMPANION, PRO_ASSISTANT


def choose_profile():
    print("\n选择 ALITA 的人设：")
    print("  1. 温柔陪伴型（默认）—— 像朋友，有温度")
    print("  2. 专业助手型 —— 简洁高效，直奔主题")
    choice = input("  输入 1/2，直接回车用默认：").strip()
    return PRO_ASSISTANT if choice == "2" else COMPANION


def main():
    setup_logging()

    profile = choose_profile()
    agent = ALITAAgent(profile=profile)

    print("=" * 56)
    print(f"   ALITA · {profile.name} 已上线")
    print(f"   风格：{profile.tone[:24]}……")
    print(f"   模型：{Config.LLM_MODEL}")
    print(f"   工具：{', '.join(agent.tools._tools.keys())}")
    print(f"   记忆：{len(agent.memory.store)} 条长期记忆")
    print("   命令：quit 退出 | reset 清空对话 | forget 清空记忆")
    print("        plan <任务> 用规划模式处理复杂任务")
    print("=" * 56)

    while True:
        question = input("\n你：").strip()
        if not question:
            continue
        low = question.lower()

        if low in ("quit", "exit", "退出"):
            print("再见，ALITA 下线。")
            break
        if low in ("reset", "清空", "重置"):
            agent.reset()
            print("已清空对话历史（长期记忆保留）。")
            continue
        if low in ("forget", "忘记"):
            agent.memory.store.clear()
            print("已清空所有长期记忆。")
            continue
        if low.startswith(("plan ", "计划 ")):
            parts = question.split(" ", 1)
            task = parts[1].strip() if len(parts) > 1 else ""
            if not task:
                print("用法：plan <任务描述>，例如 plan 帮我做一个北京三日游攻略")
                continue
            answer = agent.solve(task)
            print(f"\nALITA：{answer}")
            continue

        answer = agent.chat(question)
        print(f"\nALITA：{answer}")


if __name__ == "__main__":
    main()
