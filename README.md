# MONENG · 陪伴型智能体

从零构建陪伴型智能体系统。当前进度：**底座 ✅ → 骨架 ✅ → Profile ✅ → Memory ✅ → Planning ✅ → 循环进阶 ✅**。

## 项目结构

```
alita/
├── main.py                 # 入口：多轮对话 + plan 规划模式 + 长期记忆 + 日志
├── requirements.txt        # requests + python-dotenv
├── .env.example            # 配置模板
├── memory.json             # 长期记忆（运行后自动生成）
├── README.md
└── alita/
    ├── __init__.py
    ├── config.py           # 单一配置入口 + 日志
    ├── agent.py            # ★ MONENGAgent：组合引擎+会话+画像+记忆+规划
    ├── core/
    │   ├── llm.py          # LLM 客户端（chat + stream）
    │   ├── tools.py        # 工具结构 + 注册表
    │   ├── session.py      # 短期记忆（多轮历史 + 自动裁剪）
    │   └── agent.py        # ★ ReActAgent 引擎（无状态循环）
    ├── modules/
    │   ├── profile.py      # ★ Profile 画像
    │   ├── memory.py       # ★ Memory 长期记忆
    │   └── planning.py     # ★ Planning 任务拆解 + 反思
    └── tools/
        └── builtin.py      # 内置工具：计算/时间/天气/读文件/搜索/抓网页
```

## 快速开始

```bash
pip install -r requirements.txt
copy .env.example .env        # 编辑 .env 填入 LLM_API_KEY
python main.py
```

## 两大模式

| 模式 | 命令 | 引擎 | 适用 |
|------|------|------|------|
| 对话 | 直接输入 | ReAct | 闲聊、简单问答、单步任务 |
| 规划 | `plan <任务>` | Plan-and-Execute + Reflexion | 复杂多步任务 |

```
你：北京现在天气怎么样？              # 对话模式
你：plan 帮我做一个北京三日游攻略       # 规划模式：先列计划 → 逐步执行 → 反思改进
```

## 核心循环三层进阶

```
ReAct                  → 每轮「想→做→看」，直到能回答
Plan-and-Execute       → 先拆解任务成步骤，再逐步执行
+ Reflexion            → 执行后评估，不足就反思改进再执行
```

## 四大模块

| 模块 | 状态 | 关键文件 | 职责 |
|------|------|----------|------|
| Profile 画像 | ✅ | `modules/profile.py` | 决定 MONENG 是谁 |
| Memory 记忆 | ✅ | `modules/memory.py` | 三层记忆，长期记忆持久化 |
| Planning 规划 | ✅ | `modules/planning.py` | 任务拆解 + 反思 |
| Action 行动 | ✅ | `core/tools.py` + `tools/builtin.py` | 6 个内置工具 + 2 个记忆工具 |

## 架构思想：模块往 prompt 里「注入」内容

system prompt = **人设段** + **记忆段** + **能力段(ReAct格式)** + **工具清单**。

每个模块只负责注入自己那一段，互不依赖，各自独立开发、独立替换。

## 怎么改人设 / 记忆 / 规划

- 人设：编辑 `alita/modules/profile.py`，改 `COMPANION` / `PRO_ASSISTANT` 字段或新增预设；
- 记忆：目前是关键词检索，升级成向量检索可换 `embedding + ChromaDB`；
- 规划：`Planner.make_plan` 的 prompt 可调拆解粒度，`critique` 可调反思严格度。
