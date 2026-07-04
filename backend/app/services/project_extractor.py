import json
from app.core.embedding import get_embedding

# choose ONE (Gemini recommended since you already use it)
from app.core.llm_router import generate_completion # (you may already have this OR adapt to your Gemini client)


PROJECT_SCHEMA = """
You are an enterprise discovery engine.

Extract structured project information from meeting transcripts.

Return ONLY valid JSON in this format:

{
  "requirements": [],
  "risks": [],
  "assumptions": [],
  "stakeholders": [],
  "deliverables": [],
  "timeline": ""
}

Rules:
- Be precise, no duplication
- Do NOT add explanations
- If missing, use empty arrays or empty string
- Keep items short and enterprise-level
"""


def extract_project_state(transcript: str):

    if not transcript or len(transcript.strip()) < 10:
        return {
            "requirements": [],
            "risks": [],
            "assumptions": [],
            "stakeholders": [],
            "deliverables": [],
            "timeline": ""
        }

    prompt = f"""
{PROJECT_SCHEMA}

TRANSCRIPT:
{transcript}
"""

    try:
        # 🔥 LLM CALL (Gemini / Ollama abstraction)
        response = generate_completion(prompt)

        # clean response
        response = response.strip()

        # handle markdown-wrapped JSON
        if "```" in response:
            response = response.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response)

        # safety fallback
        return {
            "requirements": data.get("requirements", []),
            "risks": data.get("risks", []),
            "assumptions": data.get("assumptions", []),
            "stakeholders": data.get("stakeholders", []),
            "deliverables": data.get("deliverables", []),
            "timeline": data.get("timeline", "")
        }

    except Exception as e:
        # NEVER crash pipeline
        return {
            "requirements": [],
            "risks": [],
            "assumptions": [],
            "stakeholders": [],
            "deliverables": [],
            "timeline": "",
            "error": str(e)
        }