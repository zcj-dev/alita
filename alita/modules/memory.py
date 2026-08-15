"""Memory 记忆模块 —— 让 ALITA「认识你」。

四大模块里的第二个。记忆分三层：
- 短期记忆：当前对话的上下文（由 core/session.py 的 Session 负责）
- 长期记忆：跨会话持久化的事实（本模块，存 JSON 文件，重启不丢）
- 工作记忆：ReAct 执行中的临时草稿（引擎内部，不持久化）

本模块实现「长期记忆」：
- MemoryStore：读写 memory.json，重启不丢
- MemoryModule：把相关记忆渲染成「记忆段」注入 prompt
- 写入：模型通过 save_memory 工具自主决定记什么
- 读取：每次对话前自动把最近记忆注入 prompt（保证「记得」）

升级方向：关键词检索可换成向量检索（embedding + ChromaDB），语义更准。
"""
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from alita.core.tools import Tool


@dataclass
class MemoryItem:
    """一条记忆。"""
    content: str
    category: str = "general"   # 分类：fact / preference / goal / event ...
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")


class MemoryStore:
    """长期记忆的存储层：JSON 文件持久化 + 简单检索。"""

    def __init__(self, path="memory.json"):
        self.path = Path(path)
        self.items = self._load()

    def _load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return [MemoryItem(**d) for d in data]
        except Exception:
            return []

    def _save(self):
        self.path.write_text(
            json.dumps([asdict(i) for i in self.items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, content, category="general"):
        item = MemoryItem(content=content, category=category)
        self.items.append(item)
        self._save()
        return item

    def recent(self, n=10):
        """最近的 n 条记忆（陪伴型场景记忆量不大，直接注入最近一批）。"""
        return list(reversed(self.items[-n:]))

    def search(self, query, top_k=5):
        """关键词重叠打分检索。第一阶段够用，后续可换向量检索。"""
        q_terms = set(re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+", query.lower()))
        if not q_terms:
            return self.recent(top_k)
        scored = []
        for item in self.items:
            text = item.content.lower()
            score = sum(1 for t in q_terms if t in text)
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: -x[0])
        return [item for _, item in scored[:top_k]]

    def delete(self, index):
        if 0 <= index < len(self.items):
            removed = self.items.pop(index)
            self._save()
            return removed
        return None

    def clear(self):
        self.items = []
        self._save()

    def __len__(self):
        return len(self.items)


class MemoryModule:
    """把存储层包装成「能注入 prompt + 能当工具用」的模块。"""

    def __init__(self, store=None, inject_recent=10):
        self.store = store if store is not None else MemoryStore()
        self.inject_recent = inject_recent

    def render(self) -> str:
        """渲染「记忆段」注入 system prompt。没有记忆就返回空串。"""
        items = self.store.recent(self.inject_recent)
        if not items:
            return ""
        lines = [
            "## 你对用户的记忆",
            "以下是关于用户的重要信息，对话时自然地运用它们：",
        ]
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item.content}")
        return "\n".join(lines)

    def make_tools(self):
        """生成记忆相关工具：save_memory 写入、recall_memory 回忆。"""
        store = self.store

        def save(text):
            item = store.add(text)
            return f"已记住：{item.content}"

        def recall(query):
            results = store.search(query)
            if not results:
                return f"没找到关于「{query}」的记忆"
            return "\n".join(f"- {r.content}" for r in results)

        return [
            Tool(
                name="save_memory",
                description="记住关于用户的重要信息（名字、偏好、目标、经历等），输入要记住的内容，例如 save_memory[用户叫小张，喜欢喝咖啡，正在学 Python]",
                func=save,
            ),
            Tool(
                name="recall_memory",
                description="回忆关于用户的记忆，输入关键词，例如 recall_memory[用户喜欢什么]",
                func=recall,
            ),
        ]
