from docx import Document
from io import BytesIO


# ----------------------------
# SAFE STYLE HANDLER
# ----------------------------
def safe_style(doc: Document, style_name: str):
    """
    Returns style if exists in template, else fallback to Normal
    """
    try:
        _ = doc.styles[style_name]
        return style_name
    except Exception:
        return "Normal"


# ----------------------------
# TEMPLATE LOADER
# ----------------------------
def load_template(template_path: str) -> Document:
    return Document(template_path)


# ----------------------------
# ADD CONTENT TO DOCX
# ----------------------------
def add_sow_content(doc: Document, markdown: str):

    lines = markdown.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Headings
        if line.startswith("# "):
            doc.add_paragraph(
                line[2:], style=safe_style(doc, "Title")
            )

        elif line.startswith("## "):
            doc.add_paragraph(
                line[3:], style=safe_style(doc, "Heading 1")
            )

        elif line.startswith("### "):
            doc.add_paragraph(
                line[4:], style=safe_style(doc, "Heading 2")
            )

        # Bullet points
        elif line.startswith("- "):
            p = doc.add_paragraph(line[2:])
            p.style = safe_style(doc, "List Bullet")

        # Normal text
        else:
            doc.add_paragraph(
                line, style=safe_style(doc, "Normal")
            )

    return doc


# ----------------------------
# MAIN EXPORT FUNCTION
# ----------------------------
def export_docx_from_template(template_path: str, sow_markdown: str) -> bytes:

    doc = load_template(template_path)

    # Add SOW content on top of template formatting
    doc = add_sow_content(doc, sow_markdown)

    buffer = BytesIO()
    doc.save(buffer)

    return buffer.getvalue()