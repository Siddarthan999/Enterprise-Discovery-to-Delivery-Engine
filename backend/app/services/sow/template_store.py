import os
import json

TEMPLATE_DIR = "app/templates/uploads"
META_FILE = os.path.join(TEMPLATE_DIR, "templates.json")


def load_templates():
    if not os.path.exists(META_FILE):
        return []
    with open(META_FILE, "r") as f:
        return json.load(f)


def get_template_path(template_id: str | None):

    if not template_id:
        return os.path.join("app/templates", "default.docx")

    templates = load_templates()

    for t in templates:
        if t["id"] == template_id:
            return os.path.join(TEMPLATE_DIR, t["filename"])

    # fallback
    return os.path.join("app/templates", "default.docx")