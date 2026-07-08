"""
LLM API client — OpenAI-compatible Chat Completions.

Supports: OpenAI, Proma Cloud, DeepSeek, Ollama, or any OpenAI-compatible API.
Configure via .env: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
"""

import json
import httpx
from .config import Config


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    base_url: str = "",
    api_key: str = "",
) -> str:
    """
    Call an OpenAI-compatible Chat Completions API.

    Args:
        system_prompt: System message content.
        user_prompt: User message content.
        model: Model name (default: from LLM_MODEL config).
        temperature: Sampling temperature.
        max_tokens: Max tokens in response.
        base_url: API base URL override.
        api_key: API key override.

    Returns:
        The assistant's response text.
    """
    model = model or Config.LLM_MODEL
    base_url = base_url or Config.LLM_BASE_URL
    api_key = api_key or Config.LLM_API_KEY

    url = f"{base_url.rstrip('/')}/chat/completions"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    # Merge extra headers from config
    headers.update(Config.LLM_EXTRA_HEADERS)

    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': temperature,
        'max_tokens': max_tokens,
    }

    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        content = data['choices'][0]['message']['content']
        return content
    except httpx.HTTPStatusError as e:
        error_msg = f"LLM API error ({e.response.status_code}): "
        try:
            error_msg += e.response.json().get('error', {}).get('message', str(e))
        except Exception:
            error_msg += str(e)
        raise RuntimeError(error_msg) from e
    except Exception as e:
        raise RuntimeError(f"LLM API call failed: {e}") from e
