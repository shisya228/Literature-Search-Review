import json
import os
from typing import Any, Dict, List, Optional

import requests


def _base_url() -> str:
    return os.getenv("BASE_URL", "https://api.openai.com/v1")


def _model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def is_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def chat_completion(messages: List[Dict[str, str]], temperature: float = 0.2) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    url = f"{_base_url().rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": _model(),
        "messages": messages,
        "temperature": temperature,
    }
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return json.loads(content)
