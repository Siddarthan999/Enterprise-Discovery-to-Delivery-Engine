import re

def extract_entities(text: str):
    # MVP rule-based extraction (we improve in Phase 3)
    
    keywords = {
        "risks": ["risk", "compliance", "delay", "issue", "blocker"],
        "requirements": ["need", "require", "must", "should"],
        "stakeholders": ["client", "manager", "team", "lead"],
        "deliverables": ["report", "system", "workflow", "dashboard"]
    }

    entities = {
        "risks": [],
        "requirements": [],
        "stakeholders": [],
        "deliverables": []
    }

    lower = text.lower()

    for category, words in keywords.items():
        for word in words:
            if word in lower:
                entities[category].append(word)

    return entities