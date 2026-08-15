# 项目：MONENG —— 陪伴型 AI 智能体（从零手写 Agent 引擎）

## 一句话描述
从零实现具备长期记忆、任务规划与反思能力的陪伴型 AI 智能体，核心 Agent 循环（ReAct / Plan-and-Execute / Reflexion）全部手写，不依赖 LangChain 等现成框架。

## 技术亮点
- 手写 ReAct 循环引擎：Thought → Action → Observation，无状态设计，推理与记忆解耦
- 三层记忆架构：短期（会话上下文）/ 长期（JSON 持久化，跨会话记住用户信息）/ 工作（执行草稿）
- Plan-and-Execute + Reflexion：复杂任务先拆解成步骤，逐步执行后自我评估并反思改进
- 模块化系统提示词注入：Profile（人设）/ Memory（记忆）/ Planning（规划）各自独立渲染、独立替换
- 8 个工具：计算、时间、天气、读文件、联网搜索、网页抓取、记忆写入、记忆召回
- OpenAI 兼容 LLM 客户端，适配任意厂商（Groq / 通义 / DeepSeek），支持流式输出与日志回放

## 技术栈
Python 3.11 · OpenAI 兼容 API · Git / GitHub

## 项目规模
19+ 文件 · 1000+ 行 · 8 工具 · 3 大模块 · 2 种执行模式（对话 / 规划）

## 个人角色
独立完成：架构设计、核心循环引擎、记忆系统、规划与反思模块、工具系统、文档与 Git 版本管理

## 简历建议写法（一句话版）
「从零实现陪伴型 AI 智能体：手写 ReAct / Plan-and-Execute / Reflexion 循环，自研三层记忆 + 多工具调用 + 任务规划反思，适配多家大模型 API，已上线 GitHub」
