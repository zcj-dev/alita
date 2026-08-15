# MONENG · Companion AI Agent

A companion AI agent built from scratch — with long-term memory, task planning, and self-reflection. The entire agent loop (**ReAct / Plan-and-Execute / Reflexion**) is hand-written, with zero dependency on frameworks like LangChain.

## Highlights

- **Hand-written ReAct engine** — Thought → Action → Observation loop, stateless by design (reasoning decoupled from memory)
- **Three-tier memory** — short-term (conversation) / long-term (JSON persistence, remembers you across sessions) / working (execution scratchpad)
- **Plan-and-Execute + Reflexion** — complex tasks are decomposed into steps, executed, then self-critiqued and improved
- **Modular prompt injection** — Profile (persona) / Memory / Planning each render and inject their own prompt section independently
- **8 tools** — calculator, current time, weather, read file, web search, web fetch, save memory, recall memory
- **OpenAI-compatible LLM client** — works with Groq / Qwen / DeepSeek, supports streaming + logging

## Quick Start

```bash
pip install -r requirements.txt
copy .env.example .env   # fill in LLM_API_KEY
python main.py           # interactive chat (multi-turn memory)
python demo.py           # 4-scene demo for portfolio screenshots
```

## Two Modes

| Mode | Command | Engine | Use case |
|------|---------|--------|----------|
| Chat | plain input | ReAct | casual chat, simple Q&A |
| Planning | `plan <task>` | Plan-and-Execute + Reflexion | complex multi-step tasks |

## Architecture

The system prompt is assembled from independently-injected sections:

```
system prompt = persona + memory + capability (ReAct) + tools
```

| Module | File | Role |
|--------|------|------|
| Profile | `modules/profile.py` | who MONENG is |
| Memory | `modules/memory.py` | what MONENG remembers |
| Planning | `modules/planning.py` | how MONENG decomposes tasks |
| Action | `core/tools.py` + `tools/builtin.py` | what MONENG can do |

## Tech Stack

Python 3.11 · OpenAI-compatible API · Git / GitHub
