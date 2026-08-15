"""LLM 客户端：封装 OpenAI 兼容的对话接口。

设计目标：
- 不依赖任何厂商 SDK，一个 requests 搞定（Groq / 通义 / DeepSeek 通用）；
- chat() 返回完整回复（ReAct 循环用，因为要解析 Action 标记）；
- stream() 流式逐段返回（纯聊天 / 最终答案实时显示用）。
"""
import json

import requests

from alita.config import Config


class LLMClient:
    """OpenAI 兼容的聊天补全客户端。"""

    def __init__(self, base_url=None, api_key=None, model=None):
        self.base_url = (base_url or Config.LLM_BASE_URL).rstrip("/")
        self.api_key = api_key or Config.LLM_API_KEY
        self.model = model or Config.LLM_MODEL

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, messages, temperature, max_tokens):
        return {
            "model": self.model,
            "messages": messages,
            "temperature": Config.TEMPERATURE if temperature is None else temperature,
            "max_tokens": max_tokens,
        }

    def chat(self, messages, temperature=None, max_tokens=1024):
        """完整返回：一次拿整段回复。"""
        if not self.api_key:
            raise RuntimeError(
                "未配置 LLM_API_KEY。请把 .env.example 复制成 .env 并填入密钥。"
            )
        url = f"{self.base_url}/chat/completions"
        resp = requests.post(
            url,
            json=self._payload(messages, temperature, max_tokens),
            headers=self._headers(),
            timeout=60,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"LLM 调用失败（HTTP {resp.status_code}）：{resp.text}")
        return resp.json()["choices"][0]["message"]["content"]

    def stream(self, messages, temperature=None, max_tokens=1024):
        """流式返回：逐段 yield 文本（SSE 解析，边生成边吐字）。"""
        if not self.api_key:
            raise RuntimeError("未配置 LLM_API_KEY。")
        url = f"{self.base_url}/chat/completions"
        payload = self._payload(messages, temperature, max_tokens)
        payload["stream"] = True

        resp = requests.post(
            url, json=payload, headers=self._headers(), timeout=60, stream=True,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"LLM 调用失败（HTTP {resp.status_code}）：{resp.text}")

        for raw in resp.iter_lines():
            line = raw.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                delta = json.loads(data)["choices"][0]["delta"].get("content", "")
            except Exception:
                continue
            if delta:
                yield delta
