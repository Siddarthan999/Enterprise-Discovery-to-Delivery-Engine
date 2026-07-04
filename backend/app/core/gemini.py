import os
import requests
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

def check_gemini():
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            return {"status": "success"}
        return {"status": "failed", "error": r.text}

    except Exception as e:
        return {"status": "failed", "error": str(e)}