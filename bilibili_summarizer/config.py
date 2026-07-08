"""
Configuration management — loads settings from environment / .env file.

Environment variables:
    BILI_SESSDATA, BILI_JCT, BILI_DEDE_USER_ID  — Bilibili credentials
    LLM_BASE_URL, LLM_API_KEY, LLM_MODEL         — LLM API settings
    LLM_EXTRA_HEADERS                            — Optional custom headers (JSON)
    OUTPUT_DIR                                   — Default output directory
    NOTE_LANGUAGE                                — Note language (default: zh)
"""

import os
import json
from pathlib import Path

try:
    from dotenv import load_dotenv

    # Search for .env from project root upward
    env_file = Path(os.getcwd()) / ".env"
    if env_file.is_file():
        load_dotenv(env_file)
    else:
        load_dotenv()
except ImportError:
    pass


class Config:
    """Global configuration loaded from environment."""

    # ---- Bilibili credentials ----
    BILI_SESSDATA: str = os.environ.get("BILI_SESSDATA", "")
    BILI_JCT: str = os.environ.get("BILI_JCT", "")
    BILI_DEDE_USER_ID: str = os.environ.get("BILI_DEDE_USER_ID", "")

    # ---- LLM ----
    LLM_BASE_URL: str = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_API_KEY: str = os.environ.get("LLM_API_KEY", "")
    LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-4o")
    LLM_EXTRA_HEADERS: dict = {}

    # ---- Output ----
    OUTPUT_DIR: str = os.environ.get("OUTPUT_DIR", "./output")
    NOTE_LANGUAGE: str = os.environ.get("NOTE_LANGUAGE", "zh")

    @classmethod
    def load_extra_headers(cls):
        """Parse LLM_EXTRA_HEADERS from env if present."""
        raw = os.environ.get("LLM_EXTRA_HEADERS", "")
        if raw:
            try:
                cls.LLM_EXTRA_HEADERS = json.loads(raw)
            except json.JSONDecodeError:
                pass


# Parse extra headers on import
Config.load_extra_headers()
