import requests

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"
MODEL = "qwen2.5-coder:7b"

def generate_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    res = requests.post(OLLAMA_URL, json=payload)
    res.raise_for_status()

    return res.json()["response"]