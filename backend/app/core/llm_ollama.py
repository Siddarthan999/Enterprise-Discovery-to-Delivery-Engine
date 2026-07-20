import requests

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"
MODEL = "qwen2.5-coder:7b"


def generate_ollama(prompt: str) -> str:
    """
    Standard generation.
    Used for SOW generation (Markdown).
    """

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
        },
    }

    res = requests.post(OLLAMA_URL, json=payload)
    res.raise_for_status()

    return res.json()["response"]


def generate_ollama_json(prompt: str) -> str:
    """
    JSON generation.
    Used ONLY by reviewer agents.
    """

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
        },
    }

    res = requests.post(OLLAMA_URL, json=payload)
    res.raise_for_status()

    return res.json()["response"]