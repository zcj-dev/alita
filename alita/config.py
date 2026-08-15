"""全局配置：从 .env 读取环境变量，并提供安全默认值。

后续四大模块（Profile / Memory / Planning / Action）都会从这里读配置，
是整个系统的「单一配置入口」。
"""
import logging
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # 没装 python-dotenv 也不报错，直接用系统环境变量


class Config:
    """ALITA 运行配置。"""

    # —— 大模型 ——
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    # —— ReAct 循环 ——
    MAX_STEPS = int(os.getenv("MAX_STEPS", "8"))          # 最多思考-行动几轮
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))  # 0=稳定，越高越随机

    # —— 会话 ——
    MAX_HISTORY = int(os.getenv("MAX_HISTORY", "20"))     # 保留最近多少条历史


def setup_logging():
    """统一日志：控制台 + alita.log 文件，方便回看每一轮推理。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("alita.log", encoding="utf-8"),
        ],
    )
