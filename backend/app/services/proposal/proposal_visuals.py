import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "generated", "proposal_visuals")
OUTPUT_DIR = os.path.abspath(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

PRIMARY = (30, 64, 110)
ACCENT = (0, 122, 204)
LIGHT_BG = (245, 247, 250)
TEXT_DARK = (25, 25, 25)
WHITE = (255, 255, 255)


def _font(size, bold=False):
    try:
        path = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _wrap(draw, text, font, max_width):
    words = text.split()
    lines, line = [], ""
    for w in words:
        test = f"{line} {w}".strip()
        if draw.textlength(test, font=font) <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def generate_solution_diagram(solution_components: list[dict], filename: str = "solution_diagram.png") -> str | None:
    """Builds a hub-and-spoke diagram: central 'Proposed Solution' node -> one box per component."""
    items = [c for c in (solution_components or []) if c.get("name")]
    if not items:
        return None

    box_w, box_h, gap = 260, 110, 30
    cols = min(3, len(items))
    rows = -(-len(items) // cols)
    width = cols * (box_w + gap) + gap
    height = 160 + rows * (box_h + gap)

    img = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(img)
    title_font, body_font, name_font = _font(20, True), _font(14), _font(16, True)

    # central node
    cx, cy = width // 2, 70
    draw.rounded_rectangle([cx - 140, cy - 30, cx + 140, cy + 30], radius=12, fill=PRIMARY)
    draw.text((cx, cy), "PROPOSED SOLUTION", font=title_font, fill=WHITE, anchor="mm")

    for i, comp in enumerate(items):
        col, row = i % cols, i // cols
        x = gap + col * (box_w + gap)
        y = 150 + row * (box_h + gap)
        draw.line([(cx, cy + 30), (x + box_w // 2, y)], fill=ACCENT, width=2)
        draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=10, fill=LIGHT_BG, outline=ACCENT, width=2)
        name_lines = _wrap(draw, comp.get("name", ""), name_font, box_w - 20)
        desc_lines = _wrap(draw, comp.get("description", ""), body_font, box_w - 20)[:3]
        ty = y + 14
        for l in name_lines:
            draw.text((x + box_w // 2, ty), l, font=name_font, fill=PRIMARY, anchor="mm")
            ty += 20
        ty += 4
        for l in desc_lines:
            draw.text((x + box_w // 2, ty), l, font=body_font, fill=TEXT_DARK, anchor="mm")
            ty += 16

    out_path = os.path.join(OUTPUT_DIR, filename)
    img.save(out_path)
    return out_path


def generate_approach_diagram(approach_phases: list[dict], filename: str = "approach_diagram.png") -> str | None:
    """Builds a left-to-right phase roadmap from approach_phases."""
    phases = [p for p in (approach_phases or []) if p.get("title")]
    if not phases:
        return None

    box_w, box_h, gap = 220, 150, 50
    width = len(phases) * (box_w + gap) + gap
    height = 220

    img = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(img)
    title_font, obj_font, num_font = _font(16, True), _font(13), _font(20, True)

    y = 50
    for i, phase in enumerate(phases):
        x = gap + i * (box_w + gap)
        if i > 0:
            prev_x = gap + (i - 1) * (box_w + gap) + box_w
            mid_y = y + box_h // 2
            draw.line([(prev_x, mid_y), (x, mid_y)], fill=ACCENT, width=3)
            draw.polygon([(x, mid_y), (x - 10, mid_y - 6), (x - 10, mid_y + 6)], fill=ACCENT)

        draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=10, fill=PRIMARY)
        draw.ellipse([x + 10, y - 15, x + 45, y + 20], fill=ACCENT)
        draw.text((x + 27, y + 2), str(i + 1), font=num_font, fill=WHITE, anchor="mm")

        title_lines = _wrap(draw, phase.get("title", f"Phase {i+1}"), title_font, box_w - 20)
        obj_lines = _wrap(draw, phase.get("objective", ""), obj_font, box_w - 20)[:4]
        ty = y + 45
        for l in title_lines:
            draw.text((x + box_w // 2, ty), l, font=title_font, fill=WHITE, anchor="mm")
            ty += 20
        ty += 4
        for l in obj_lines:
            draw.text((x + box_w // 2, ty), l, font=obj_font, fill=WHITE, anchor="mm")
            ty += 15

    out_path = os.path.join(OUTPUT_DIR, filename)
    img.save(out_path)
    return out_path