import requests
import os

API_KEY = os.getenv("GEMINI_API_KEY")

def extract_entities(text):
    prompt = f"""
Extract structured entities:

Return JSON:
{{
  "projects": [],
  "deliverables": [],
  "stakeholders": [],
  "risks": [],
  "requirements": [],
  "timelines": []
}}

TEXT:
{text}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

    res = requests.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}]
    })

    return res.json()