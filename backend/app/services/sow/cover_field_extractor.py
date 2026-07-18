"""
Derives cover-page fields (company name, sub-headline, etc.) automatically
from whatever context is available — the structured discovery state, the
generated SOW markdown, or the raw transcript — instead of requiring the
user to type them in manually.

Priority order (first non-empty match wins):
  1. Known keys on the structured `state` object produced by discovery.
  2. Explicit-label patterns inside the generated SOW markdown
     (e.g. "Client:", "Company:", "Prepared for:").
  3. Explicit-label patterns inside the raw transcript.

If none of these find anything, the field is left empty and the
template's original placeholder text is left untouched by
apply_cover_page_fields (this is a deliberate no-op, not a crash).
"""

import re

# Common key names a discovery/state-extraction step might use for the
# client/company. Adjust this list once you confirm what DiscoveryPanel
# actually produces.
_STATE_COMPANY_KEYS = [
    "company_name", "companyName",
    "client_name", "clientName",
    "client", "company", "organization", "organisation",
]

_STATE_SUBHEADLINE_KEYS = [
    "sub_headline", "subHeadline",
    "project_title", "projectTitle",
    "engagement_name", "engagementName",
    "engagement_title", "title",
]

# Regex patterns for pulling a labeled value out of markdown or transcript
# text, e.g. "Client: Acme Corp" or "Prepared for: Acme Corp".
_LABEL_PATTERNS = [
    re.compile(r"(?im)^\**client\**\s*[:\-]\s*(.+)$"),
    re.compile(r"(?im)^\**company\**\s*[:\-]\s*(.+)$"),
    re.compile(r"(?im)^\**prepared for\**\s*[:\-]\s*(.+)$"),
    re.compile(r"(?im)^\**customer\**\s*[:\-]\s*(.+)$"),
]

_HEADING_FOR_PATTERN = re.compile(r"(?im)^#\s*statement of work for\s+(.+)$")


def _first_state_match(state: dict | None, keys: list[str]) -> str:
    if not state:
        return ""
    for key in keys:
        value = state.get(key)
        if value and isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _first_regex_match(text: str | None, patterns: list[re.Pattern]) -> str:
    if not text:
        return ""
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip().strip("*").strip()
    return ""


def derive_company_name(state: dict | None, sow_markdown: str | None,
                         transcript: str | None) -> str:
    # 1. Structured state (most reliable — already extracted by discovery)
    value = _first_state_match(state, _STATE_COMPANY_KEYS)
    if value:
        return value

    # 2. "# Statement of Work for <Company>" heading style
    if sow_markdown:
        match = _HEADING_FOR_PATTERN.search(sow_markdown)
        if match:
            return match.group(1).strip()

    # 3. Labeled lines in the SOW markdown
    value = _first_regex_match(sow_markdown, _LABEL_PATTERNS)
    if value:
        return value

    # 4. Labeled lines in the raw transcript
    value = _first_regex_match(transcript, _LABEL_PATTERNS)
    if value:
        return value

    return ""


def derive_sub_headline(state: dict | None, sow_markdown: str | None) -> str:
    # 1. Structured state
    value = _first_state_match(state, _STATE_SUBHEADLINE_KEYS)
    if value:
        return value

    # 2. Fall back to the first H2 in the generated SOW (often something
    #    like "## Executive Summary" isn't useful, so specifically look
    #    for the first heading that ISN'T a generic section name).
    generic_headings = {"executive summary", "overview", "introduction"}
    if sow_markdown:
        for line in sow_markdown.splitlines():
            line = line.strip()
            if line.startswith("## "):
                heading_text = line[3:].strip()
                if heading_text.lower() not in generic_headings:
                    return heading_text

    return ""


def derive_cover_fields(state: dict | None = None,
                         sow_markdown: str | None = None,
                         transcript: str | None = None) -> dict:
    return {
        "company_name": derive_company_name(state, sow_markdown, transcript),
        "sub_headline": derive_sub_headline(state, sow_markdown),
    }