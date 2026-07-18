from docx import Document


def extract_sections(docx_path: str):
    doc = Document(docx_path)

    sections = []
    full_text = []

    for para in doc.paragraphs:
        text = para.text.strip()

        if not text:
            continue

        full_text.append(text)

        # heuristic: headings are usually bold or short
        if len(text) < 80:
            if text.isupper() or para.style.name.startswith("Heading"):
                sections.append(text)

    return {
        "sections": list(dict.fromkeys(sections)),
        "raw_text": full_text
    }