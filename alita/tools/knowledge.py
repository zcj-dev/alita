"""知识库检索工具 —— 让 MONENG 能读懂你的本地文档（RAG）。

RAG = Retrieval-Augmented Generation（检索增强生成）：
先检索相关文档片段，再让模型基于片段回答，避免「瞎编」。

用法：
1. 把你的文档（.txt / .md）放进项目的 docs/ 目录
2. MONENG 会自动获得 search_docs 工具
3. 问「search_docs[关键词]」即可检索

当前用关键词打分（零依赖、开箱即用）；
可升级为向量检索（embedding + ChromaDB），语义匹配更准。
"""
import re
from pathlib import Path

from alita.core.tools import Tool

DOCS_DIR = Path("docs")


def _load_chunks(docs_dir=DOCS_DIR, chunk_size=300):
    """加载 docs/ 下的 txt/md，按段落分块（太长的段落再切）。"""
    chunks = []
    if not docs_dir.exists():
        return chunks
    for f in sorted(docs_dir.glob("*")):
        if f.suffix.lower() not in (".txt", ".md"):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for para in text.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size):
                    chunks.append({"source": f.name, "text": para[i:i + chunk_size]})
            else:
                chunks.append({"source": f.name, "text": para})
    return chunks


def search_docs(query, docs_dir=DOCS_DIR, top_k=3):
    """关键词打分检索，返回最相关的文档片段。"""
    chunks = _load_chunks(docs_dir)
    if not chunks:
        return "docs/ 目录为空或不存在。把 .txt/.md 文档放进 docs/ 目录后即可检索。"
    terms = set(re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+", query.lower()))
    if not terms:
        return "请提供有效的检索关键词。"
    scored = []
    for c in chunks:
        text = c["text"].lower()
        score = sum(1 for t in terms if t in text)
        if score > 0:
            scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        return f"没有找到与「{query}」相关的内容。"
    return "\n\n".join(f"[{c['source']}] {c['text'][:200]}" for _, c in scored[:top_k])


def make_knowledge_tools(docs_dir=DOCS_DIR):
    """生成知识库检索工具。"""
    def search(q):
        return search_docs(q, docs_dir)

    return [Tool(
        name="search_docs",
        description="检索本地知识库（docs 目录下的文档），输入关键词，例如 search_docs[如何配置 API]",
        func=search,
    )]
