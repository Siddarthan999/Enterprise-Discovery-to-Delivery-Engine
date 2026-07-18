import os
import uuid
import json

TEMPLATE_DIR = "app/templates/uploads"
META_FILE = os.path.join(TEMPLATE_DIR, "templates.json")

os.makedirs(TEMPLATE_DIR, exist_ok=True)


def load_templates():
    if not os.path.exists(META_FILE):
        return []
    with open(META_FILE, "r") as f:
        return json.load(f)


def save_templates(templates):
    with open(META_FILE, "w") as f:
        json.dump(templates, f, indent=2)


def store_file(file):
    template_id = str(uuid.uuid4())
    filename = f"{template_id}.docx"
    path = os.path.join(TEMPLATE_DIR, filename)

    with open(path, "wb") as f:
        f.write(file)

    return template_id, filename, path