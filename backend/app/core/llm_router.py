from app.core.llm_gemini import generate_gemini
from app.core.llm_ollama import generate_ollama

LLM_PROVIDER = "ollama"  # "gemini" | "ollama" | "auto"

def generate_completion(prompt: str) -> str:

    # ---------------- FORCE MODES ----------------
    if LLM_PROVIDER == "gemini":
        return generate_gemini(prompt)

    if LLM_PROVIDER == "ollama":
        return generate_ollama(prompt)

    # ---------------- AUTO MODE ----------------
    try:
        return generate_gemini(prompt)

    except Exception as e:
        print("⚠️ Gemini failed, switching to Ollama fallback:", str(e))

        try:
            return generate_ollama(prompt)
        except Exception as e2:
            raise Exception(f"Both LLMs failed: {str(e2)}")