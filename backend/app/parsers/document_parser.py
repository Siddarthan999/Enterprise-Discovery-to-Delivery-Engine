from pypdf import PdfReader
import docx
from pptx import Presentation
import pandas as pd
import os
import re

# ---------------- CLEAN TEXT ----------------
def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.replace("\x00", "").strip()


# ---------------- TXT ----------------
def parse_txt(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    return {
        "title": os.path.basename(file_path),
        "content": clean_text(text),
        "type": "txt"
    }

# ---------------- PDF ----------------
def parse_pdf(file_path):
    reader = PdfReader(file_path)
    text_pages = []

    for page in reader.pages:
        try:
            extracted = page.extract_text()
            if extracted:
                text_pages.append(extracted)
        except Exception:
            continue

    text = "\n".join(text_pages)

    # fallback guard
    if len(text.strip()) < 50:
        text = "PDF_TEXT_EXTRACTION_FAILED_OR_SCANNED_DOCUMENT"

    return {
        "title": os.path.basename(file_path),
        "content": clean_text(text),
        "type": "pdf"
    }

# ---------------- DOCX ----------------
def parse_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([p.text for p in doc.paragraphs])

    return {
        "title": os.path.basename(file_path),
        "content": clean_text(text),
        "type": "docx"
    }


# ---------------- PPTX ----------------
def parse_pptx(file_path):
    prs = Presentation(file_path)
    text = []

    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text.append(shape.text)

    return {
        "title": os.path.basename(file_path),
        "content": clean_text("\n".join(text)),
        "type": "pptx"
    }


# ---------------- CSV ----------------
def parse_csv(file_path):
    df = pd.read_csv(file_path)
    text = df.astype(str).to_string(index=False)

    return {
        "title": os.path.basename(file_path),
        "content": clean_text(text),
        "type": "csv"
    }


# ---------------- EXCEL ----------------
def parse_excel(file_path):
    df = pd.read_excel(file_path)
    text = df.astype(str).to_string(index=False)

    return {
        "title": os.path.basename(file_path),
        "content": clean_text(text),
        "type": "excel"
    }


# ---------------- MARKDOWN ----------------
def parse_md(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    return {
        "title": os.path.basename(file_path),
        "content": clean_text(text),
        "type": "md"
    }


# ---------------- EMAIL ----------------
def parse_eml(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    return {
        "title": os.path.basename(file_path),
        "content": clean_text(text),
        "type": "eml"
    }


# ---------------- .vtt (CAPTIONS) ----------------
def parse_vtt(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    # Remove WEBVTT header + timestamps
    cleaned_lines = []

    for line in raw.split("\n"):
        line = line.strip()

        # skip headers / timestamps / empty lines
        if (
            line.startswith("WEBVTT")
            or "-->" in line
            or re.match(r"^\d+$", line)
            or line == ""
        ):
            continue

        # remove speaker tags like <v Name>
        line = re.sub(r"<v .*?>", "", line)
        line = line.replace("</v>", "")

        cleaned_lines.append(line)

    return {
        "title": os.path.basename(file_path),
        "content": " ".join(cleaned_lines),
        "type": "vtt"
    }

# ---------------- ROUTER ----------------
def parse_document(file_path):
    ext = file_path.split(".")[-1].lower()

    type_map = {
        "txt": "txt",
        "pdf": "pdf",
        "docx": "docx",
        "pptx": "pptx",
        "csv": "csv",
        "xls": "excel",
        "xlsx": "excel",
        "md": "md",
        "eml": "eml",
        "vtt": "vtt"
    }

    if ext == "txt":
        doc = parse_txt(file_path)
    elif ext == "pdf":
        doc = parse_pdf(file_path)
    elif ext == "docx":
        doc = parse_docx(file_path)
    elif ext == "pptx":
        doc = parse_pptx(file_path)
    elif ext == "csv":
        doc = parse_csv(file_path)
    elif ext in ["xls", "xlsx"]:
        doc = parse_excel(file_path)
    elif ext == "md":
        doc = parse_md(file_path)
    elif ext == "eml":
        doc = parse_eml(file_path)
    elif ext == "vtt":
        doc = parse_vtt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    doc["type"] = type_map.get(ext, ext)
    return doc

# You now have a unified enterprise ingestion parser:
"""
PDF     → text
DOCX    → text
PPTX    → slides → text
CSV     → table → text
Excel   → sheet → text
MD      → raw text
EML     → email content
"""