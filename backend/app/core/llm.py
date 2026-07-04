import os
import requests
import google.generativeai as genai

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  
# options: "gemini" | "ollama"

# ---------------- GEMINI ----------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# ---------------- OLLAMA ----------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = "qwen2.5-coder:7b"


def _call_gemini(prompt: str) -> str:
    return gemini_model.generate_content(prompt).text


def _call_ollama(prompt: str) -> str:
    res = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    res.raise_for_status()
    return res.json()["response"]


def generate_completion(prompt: str) -> str:
    if LLM_PROVIDER == "ollama":
        return _call_ollama(prompt)

    return _call_gemini(prompt)