"""内置工具：计算器、当前时间、天气、读文件、联网搜索。

- calculator：安全求值，只允许数字和四则运算，杜绝任意代码执行；
- current_time：返回当前时间；
- get_weather：走 wttr.in 免费接口，无需密钥；
- read_file：读本地文本文件（限制大小、只读文本，安全可控）；
- search_web：走 DuckDuckGo 免费接口，无需密钥（正式项目可换 SerpAPI/Brave）。
"""
import ast
import operator
import re
from datetime import datetime
from pathlib import Path

import requests

from alita.core.tools import Tool, ToolRegistry


# —— 计算器：白名单式安全求值 ——
_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}


def _safe_eval(expr: str):
    """只允许数字、括号和 + - * / ** %，杜绝任意代码执行。"""
    expr = re.sub(r"[^0-9+\-*/%(). ]", "", expr)
    node = ast.parse(expr, mode="eval")

    def walk(n):
        if isinstance(n, ast.Expression):
            return walk(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _SAFE_OPS:
            return _SAFE_OPS[type(n.op)](walk(n.left), walk(n.right))
        raise ValueError("表达式包含不支持的运算")

    return walk(node)


def calc(expr: str):
    return f"{expr} = {_safe_eval(expr)}"


def now(_: str = ""):
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def weather(city: str):
    url = f"https://wttr.in/{city}?format=%l:+%c+%t+%w+%h"
    resp = requests.get(url, timeout=15)
    return resp.text.strip()


# —— 读文件：只读文本、限制大小 ——
def read_file(path: str):
    p = Path(path.strip()).expanduser()
    if not p.exists():
        return f"错误：文件不存在 {path}"
    if not p.is_file():
        return f"错误：不是文件 {path}"
    if p.stat().st_size > 100_000:
        return "错误：文件超过 100KB，请换个小文件或先分割"
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:5000]
    except Exception as e:
        return f"读取失败：{e}"


# —— 联网搜索：DuckDuckGo 免费接口 ——
def search_web(query: str):
    resp = requests.get(
        "https://api.duckduckgo.com/",
        params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
        timeout=15,
    )
    data = resp.json()
    results = []
    for item in data.get("RelatedTopics", [])[:8]:
        if "Text" in item:
            results.append(item["Text"])
        elif "Topics" in item:  # 分类结果，再往里取
            for sub in item["Topics"][:3]:
                if "Text" in sub:
                    results.append(sub["Text"])
    if not results:
        return f"没有找到关于「{query}」的结果"
    return "\n".join(f"- {r}" for r in results[:5])


# —— 抓网页：简化版文本提取（正式项目可换 BeautifulSoup） ——
def get_http(url: str):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    text = re.sub(r"<[^>]+>", " ", resp.text)
    text = re.sub(r"\s+", " ", text)
    return text[:3000]


def register_builtin_tools(registry: ToolRegistry):
    """把内置工具注册进给定的注册表。"""
    registry.register(Tool(
        name="calculator",
        description="做数学计算，输入一个算式，例如 calculator[3*(4+5)]",
        func=calc,
    ))
    registry.register(Tool(
        name="current_time",
        description="获取当前日期和时间，输入留空，例如 current_time[]",
        func=now,
    ))
    registry.register(Tool(
        name="get_weather",
        description="查询某城市天气，输入城市名（中英文均可），例如 get_weather[Beijing]",
        func=weather,
    ))
    registry.register(Tool(
        name="read_file",
        description="读取本地文本文件内容，输入绝对或相对路径，例如 read_file[README.md]",
        func=read_file,
    ))
    registry.register(Tool(
        name="search_web",
        description="联网搜索，输入关键词，例如 search_web[Python 装饰器]",
        func=search_web,
    ))
    registry.register(Tool(
        name="get_http",
        description="抓取网页内容，输入网址，例如 get_http[https://example.com]",
        func=get_http,
    ))
