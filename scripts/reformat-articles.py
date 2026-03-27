#!/usr/bin/env python3
"""
Smart article reformatter for OrgoniteGuide.
Fixes formatting issues in PDF-extracted markdown files:
- ALL CAPS section headers → ## Markdown headings
- Implicit section breaks → proper headings
- Academic front matter (title pages, acknowledgements) → stripped/condensed
- Magazine TOC → removed
- Copyright/legal boilerplate → stripped
- Numbered section headers → ## headings
- Multi-column garble markers → best-effort fix
"""

import re
import os
from pathlib import Path

ARTICLES_DIR = Path(__file__).parent.parent / "src" / "content" / "articles"

# ── Boilerplate patterns to strip entirely ──────────────────────────────────

STRIP_LINE_PATTERNS = [
    # Academic dissertation front matter
    r"submitted to (the Faculty|Holos|the Graduate)",
    r"in partial fulfillment",
    r"for the degree of",
    r"DOCTOR OF (THEOLOGY|PHILOSOPHY|SCIENCE|EDUCATION|MEDICINE)",
    r"All Rights Reserved",
    r"Copyright by .{3,60}20\d\d",
    r"^Copyright .{3,80}$",
    r"The work reported in this thesis is original",
    r"carried out by me solely",
    r"Graduate Seminary",
    r"Holos University",
    # Magazine repeated headers/footers
    r"Modern Orgone Electronic Magazine",
    r"Wizzers Workshop",
    r"Wizzers Desk",
    r"©\d{4}[-–]\d{4}",
    r"opt-in research journal",
    r"independently published by",
    r"contributed articles may have copyrights",
    r"reprinted with permission",
    r"in accordance with fair use",
    r"views expressed are the opinion",
    r"intellectual/artistic property",
    # Page headers/footers
    r"^Free-eBooks\.net",
    r"Free eBooks? (at|from) Free-eBooks",
    r"Share this (eBook|book) with",
    r"For your own Unlimited Reading",
    r"This book was distributed courtesy of",
    r"visit.*Free-eBooks\.net",
    # TOC dot-leader entries (e.g. "Chapter 1.......................1" or "Background......3")
    r"\.{4,}\s*\d+\s*$",
    # SPSS/statistical command output (raw dissertation appendix data)
    r"^#{0,3}\s*/(?:Method|Criteria|Plot|WsFactor|WsDesign|Design|Print|Save|Emmeans)\s*=",
    r"^#{0,3}\s*(?:Syntax\s+)?(?:GLM|UNIANOVA|ONEWAY|MANOVA)\b",
    r"^#{0,3}\s*/(?:WSFACTOR|WSDESIGN|CONTRAST|LMATRIX|KMATRIX)\b",
    # Generic PDF artifacts
    r"^\s*\[?image\]?\s*$",
    r"^\s*\(see (image|figure|diagram)\)\s*$",
    r"^Figure \d+\.?\s*$",
    r"^\s*---+\s*$",   # bare dashes (already handled)
    r"^_{3,}\s*$",
]

STRIP_BLOCK_PATTERNS = [
    # Strip long copyright boilerplate blocks (magazine copyright)
    r"©\d{4}.*?all rights reserved.*?\n",
]

# ── Heading detection patterns ───────────────────────────────────────────────

# Lines that should become ## headings
H2_PATTERNS = [
    # ALL CAPS heading (3+ words, all uppercase letters, spaces, punctuation)
    r"^[A-Z][A-Z\s\-/&:,']{8,}[A-Z]$",
    # Chapter headings
    r"^(Chapter|CHAPTER)\s+([IVX]+|\d+)[\s:\.]*(.*)$",
    # Numbered sections
    r"^\d+\.\s{1,3}[A-Z][A-Za-z\s]{5,}$",
    # Roman numeral sections
    r"^[IVX]+\.\s+[A-Z][A-Za-z\s]{3,}$",
    # "SECTION N:" or "PART N:"
    r"^(SECTION|PART|APPENDIX)\s+[A-Z\d]+",
]

# Lines that should become ### headings (sub-sections)
H3_PATTERNS = [
    # "Word Word Word" (title-case, short, standalone)
    # handled contextually below
]


def is_all_caps_heading(line: str) -> bool:
    """True if line looks like an ALL CAPS section heading."""
    stripped = line.strip()
    if len(stripped) < 4 or len(stripped) > 100:
        return False
    # Must have at least 2 words
    words = stripped.split()
    if len(words) < 2:
        return False
    # Count uppercase vs total alpha chars
    alpha = [c for c in stripped if c.isalpha()]
    if not alpha:
        return False
    upper_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
    # At least 85% uppercase
    if upper_ratio < 0.85:
        return False
    # Exclude lines that are clearly prose (have common lowercase words)
    lower_words = {"and", "or", "the", "of", "in", "a", "an", "is", "to", "for", "with", "by"}
    if any(w.lower() in lower_words for w in words if w.islower()):
        return False
    return True


def is_implicit_heading(line: str, prev_blank: bool, next_blank: bool) -> bool:
    """
    Detect a line that looks like a section heading by context:
    - Short (< 70 chars)
    - Title-case or sentence-case
    - Surrounded by blank lines on at least one side
    - Ends without a period (not a sentence)
    - Not too long to be a paragraph starter
    """
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) > 80 or len(stripped) < 5:
        return False
    if stripped.endswith('.') or stripped.endswith(','):
        return False
    # Must start with uppercase
    if not stripped[0].isupper():
        return False
    # Must look like a title (few words, mostly capitalized)
    words = stripped.split()
    if len(words) > 10:
        return False
    if len(words) < 2:
        return False
    # At least half the words should start with uppercase OR be short connectors
    short_connectors = {"a", "an", "and", "or", "the", "of", "in", "to", "for",
                        "with", "by", "on", "at", "as", "is", "its", "from"}
    cap_words = sum(1 for w in words if w[0].isupper() or w.lower() in short_connectors)
    if cap_words / len(words) < 0.6:
        return False
    # Must be surrounded by blank lines
    if not (prev_blank or next_blank):
        return False
    return True


def _is_attached_heading(line: str, next_line: str) -> bool:
    """
    Detect a heading that runs directly into the next paragraph (no blank line between).
    Examples:
      "What is Orgone?"           → ## heading
      "Orgone is life energy"     → ## heading
      "Orgone is generated from order"  → ## heading
    Not a heading:
      "Orgone was conceived as the anti-entropic principle..."  (too long, prose)
    """
    if not line:
        return False
    # Must be short — real headings are concise
    words = line.split()
    if len(words) > 8 or len(line) > 70:
        return False
    if len(words) < 2:
        return False
    # Must start with uppercase
    if not line[0].isupper():
        return False
    # Skip if ends with comma/semicolon (mid-sentence fragment)
    if line.endswith(',') or line.endswith(';'):
        return False
    # If ends with period it's likely a sentence, not a heading
    if line.endswith('.') and len(words) > 4:
        return False
    # Question headings are almost always real headings
    if line.endswith('?'):
        return True
    # For declarative headings, next line must be a substantial paragraph
    if len(next_line.split()) >= 10:
        return True
    return False


def clean_boilerplate(lines: list[str]) -> list[str]:
    """Remove boilerplate lines from the beginning and end of content."""
    result = []
    for line in lines:
        stripped = line.strip()
        should_strip = False
        for pat in STRIP_LINE_PATTERNS:
            if re.search(pat, stripped, re.IGNORECASE):
                should_strip = True
                break
        if not should_strip:
            result.append(line)
    return result


def strip_front_matter(lines: list[str]) -> tuple[list[str], str]:
    """
    Strip academic/book front matter from the start of the document.
    Returns (cleaned_lines, front_matter_summary).
    Front matter = title page, copyright, acknowledgements (first ~50 lines).
    """
    # Find where the "real" content starts
    # Indicators of real content: long paragraphs, section headings like ABSTRACT or INTRODUCTION
    # that we want to keep, or more than 3 consecutive lines of prose

    # Detect known front-matter sections to skip
    front_matter_sections = {
        "acknowledgements", "acknowledgment", "acknowledgments",
        "dedication", "preface", "foreword",
    }

    # Keep content from ABSTRACT onwards for academic papers
    keep_from_sections = {
        "abstract", "introduction", "overview", "summary",
        "background", "methodology", "results", "discussion",
        "conclusion", "references", "bibliography",
    }

    # Check if this looks like an academic paper (has dissertation-style content)
    full_text = "\n".join(lines[:80]).lower()
    is_academic = any(phrase in full_text for phrase in [
        "dissertation", "thesis", "submitted to", "degree of doctor",
        "abstract", "methodology", "hypothesis",
    ])

    if not is_academic:
        return lines, ""

    # For academic papers, find the ABSTRACT section and start there
    abstract_idx = None
    intro_idx = None

    for i, line in enumerate(lines):
        stripped = line.strip().upper()
        if stripped in ("ABSTRACT", "EXECUTIVE SUMMARY", "SUMMARY"):
            abstract_idx = i
            break
        if stripped in ("INTRODUCTION", "1. INTRODUCTION", "I. INTRODUCTION", "OVERVIEW"):
            if intro_idx is None:
                intro_idx = i

    start_idx = abstract_idx or intro_idx or 0

    if start_idx > 5:
        skipped = lines[:start_idx]
        # Build a brief front matter note
        title_lines = []
        for line in skipped[:10]:
            s = line.strip()
            if s and not re.search(r"submitted|fulfillment|degree|copyright|seminary|holos|university", s, re.I):
                if len(s) > 3 and not s.startswith("_"):
                    title_lines.append(s)

        front_note = ""
        if title_lines:
            first_title = title_lines[0] if title_lines else ""
            # Find author line
            author = ""
            for line in skipped[1:8]:
                s = line.strip()
                if s and len(s.split()) <= 5 and s[0].isupper() and not re.search(r"copyright|all rights|©", s, re.I):
                    if first_title and s != first_title:
                        author = s
                        break
            if first_title or author:
                front_note = f"> **{first_title}**"
                if author:
                    front_note += f"\n> *{author}*"
                front_note += "\n\n"

        return lines[start_idx:], front_note

    return lines, ""


def convert_headings(lines: list[str]) -> list[str]:
    """Convert ALL CAPS and implicit headings to markdown ## headings."""
    result = []
    n = len(lines)

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Already a heading
        if stripped.startswith("#"):
            result.append(line)
            continue

        # Skip if inside a code block
        if stripped.startswith("```") or stripped.startswith("    "):
            result.append(line)
            continue

        prev_blank = (i == 0) or (lines[i - 1].strip() == "")
        next_blank = (i == n - 1) or (lines[i + 1].strip() == "")

        # Check ALL CAPS heading
        if is_all_caps_heading(stripped):
            # Title-case it
            titled = stripped.title()
            # Fix some known all-caps abbreviations back
            titled = re.sub(r'\bDhea\b', 'DHEA', titled)
            titled = re.sub(r'\bDna\b', 'DNA', titled)
            titled = re.sub(r'\bRna\b', 'RNA', titled)
            titled = re.sub(r'\bEm\b', 'EM', titled)
            titled = re.sub(r'\bRf\b', 'RF', titled)
            titled = re.sub(r'\bOd\b', 'Od', titled)
            titled = re.sub(r'\bUfo\b', 'UFO', titled)
            titled = re.sub(r'\bUfos\b', 'UFOs', titled)
            titled = re.sub(r'\bPor\b', 'POR', titled)
            titled = re.sub(r'\bDor\b', 'DOR', titled)
            # Add blank line before if not already there
            if result and result[-1].strip() != "":
                result.append("")
            result.append(f"## {titled}")
            if next_blank is False:
                result.append("")
            continue

        # Check numbered section heading: "1. Something" or "1.1 Something"
        m = re.match(r'^(\d+(?:\.\d+)?)\.\s+([A-Z][A-Za-z\s\-,]{3,60})$', stripped)
        if m and prev_blank:
            num, title = m.group(1), m.group(2).strip()
            depth = "##" if "." not in num else "###"
            if result and result[-1].strip() != "":
                result.append("")
            result.append(f"{depth} {num}. {title}")
            if not next_blank:
                result.append("")
            continue

        # Check Roman numeral section: "IV. Something"
        m = re.match(r'^([IVX]{1,5})\.\s+([A-Z][A-Za-z\s\-,]{3,60})$', stripped)
        if m and prev_blank:
            if result and result[-1].strip() != "":
                result.append("")
            result.append(f"## {stripped}")
            if not next_blank:
                result.append("")
            continue

        # Check "Chapter N" or "CHAPTER N"
        m = re.match(r'^(Chapter|CHAPTER)\s+([IVX]+|\d+)[\s:\.]*(.*)$', stripped, re.I)
        if m:
            chapter_num = m.group(2)
            chapter_title = m.group(3).strip() if m.group(3).strip() else f"Chapter {chapter_num}"
            if result and result[-1].strip() != "":
                result.append("")
            result.append(f"## Chapter {chapter_num}: {chapter_title}" if chapter_title != f"Chapter {chapter_num}" else f"## Chapter {chapter_num}")
            result.append("")
            continue

        # Contextual implicit heading detection (surrounded by blanks)
        if (prev_blank and next_blank and
                is_implicit_heading(stripped, prev_blank, next_blank)):
            if result and result[-1].strip() != "":
                result.append("")
            result.append(f"## {stripped}")
            result.append("")
            continue

        # Attached sub-heading detection: short line immediately before a long paragraph.
        # Triggers when previous line ended a paragraph (blank OR ends with period/colon)
        # e.g. "What is Orgone?" or "Orgone is life energy" on its own line
        prev_line_content = (lines[i - 1].strip() if i > 0 else "")
        prev_ends_para = prev_blank or prev_line_content.endswith(('.', ':'))
        if prev_ends_para and not next_blank and not stripped.startswith('#'):
            next_line_content = lines[i + 1].strip() if i + 1 < n else ""
            if _is_attached_heading(stripped, next_line_content):
                if result and result[-1].strip() != "":
                    result.append("")
                result.append(f"## {stripped}")
                result.append("")
                continue

        result.append(line)

    return result


def _is_prose_line(s: str) -> bool:
    """Return True if a line looks like body prose (not a heading/list/blank)."""
    if not s:
        return False
    if s.startswith(('#', '-', '*', '>', '|', '!', '[')):
        return False
    if re.match(r'^\d+[\.\)]\s', s):      # numbered list
        return False
    if re.match(r'^https?://', s):        # bare URL
        return False
    return True


def _looks_like_heading_candidate(s: str) -> bool:
    """Return True if a short line looks more like a heading than a sentence fragment."""
    words = s.split()
    if len(words) > 10:
        return False
    # Ends without punctuation AND is title-case-ish
    if s[-1] in '.!?,;:':
        return False
    cap_count = sum(1 for w in words if w and w[0].isupper())
    return cap_count / len(words) >= 0.6


def _remove_false_blank_lines(lines: list[str]) -> list[str]:
    """
    Remove blank lines that appear mid-sentence due to PDF column/page breaks.
    If line[i] ends without sentence punctuation AND line[i+1] is blank AND
    line[i+2] starts with a lowercase letter → the blank is a false paragraph
    boundary; remove it so the join pass can stitch the sentence together.
    """
    result = list(lines)
    changed = True
    while changed:
        changed = False
        out = []
        i = 0
        while i < len(result):
            line = result[i]
            stripped = line.strip()
            # Check: prose line ending without punct, then blank, then lowercase continuation
            if (stripped and _is_prose_line(stripped)
                    and stripped[-1] not in '.!?:;"\u201d\u2019'
                    and len(stripped.split()) >= 3
                    and not _looks_like_heading_candidate(stripped)
                    and not stripped.startswith('#')
                    and i + 2 < len(result)
                    and result[i + 1].strip() == ""          # blank line follows
                    and result[i + 2].strip()                # non-blank after blank
                    and result[i + 2].strip()[0].islower()   # starts lowercase
                    and _is_prose_line(result[i + 2].strip())):
                # Drop the blank line (i+1), keep current and continuation
                out.append(line)
                i += 2  # skip the blank
                changed = True
            else:
                out.append(line)
                i += 1
        result = out
    return result


def fix_paragraph_breaks(lines: list[str]) -> list[str]:
    """
    PDF text often has hard line breaks mid-sentence (from column layout or
    narrow PDF columns). Joins continuation lines into proper paragraphs.

    Rules for joining line[i] → line[i+1]:
    1. Remove false blank lines (PDF column breaks mid-sentence)
    2. Hyphenated word at line end → join and remove hyphen
    3. Line ends WITHOUT sentence-ending punctuation (.!?:;) AND
       - next line is non-blank prose AND
       - current line is not a standalone heading candidate (short + title-case)
    """
    lines = _remove_false_blank_lines(lines)
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blanks, headings, special lines immediately
        if not stripped or not _is_prose_line(stripped):
            result.append(line)
            i += 1
            continue

        # Peek at next non-trivial context
        next_stripped = lines[i + 1].strip() if i + 1 < len(lines) else ""

        # Rule 1: PDF hyphenation — join hyphenated word
        if stripped.endswith('-') and not stripped.endswith('--'):
            if next_stripped and _is_prose_line(next_stripped):
                result.append(stripped[:-1] + next_stripped)
                i += 2
                continue

        # Rule 2: Mid-sentence line break — join if line ends without sentence punct
        if (next_stripped
                and _is_prose_line(next_stripped)
                and stripped[-1] not in '.!?:;"\u201d\u2019'   # not end of sentence
                and len(stripped.split()) >= 3                  # not a 1-2 word fragment
                and not _looks_like_heading_candidate(stripped) # not a heading
        ):
            # Extra guard: don't join if current line already has a heading marker
            if not stripped.startswith('#'):
                result.append(stripped + ' ' + next_stripped)
                i += 2
                continue

        result.append(line)
        i += 1

    # Second pass — catches joins revealed by the first pass
    # (e.g. a newly joined line may itself need joining with the next line)
    result2 = []
    i = 0
    while i < len(result):
        line = result[i]
        stripped = line.strip()
        if not stripped or not _is_prose_line(stripped):
            result2.append(line); i += 1; continue
        next_stripped = result[i + 1].strip() if i + 1 < len(result) else ""
        if stripped.endswith('-') and not stripped.endswith('--'):
            if next_stripped and _is_prose_line(next_stripped):
                result2.append(stripped[:-1] + next_stripped); i += 2; continue
        if (next_stripped and _is_prose_line(next_stripped)
                and stripped[-1] not in '.!?:;"\u201d\u2019'
                and len(stripped.split()) >= 3
                and not _looks_like_heading_candidate(stripped)
                and not stripped.startswith('#')):
            result2.append(stripped + ' ' + next_stripped); i += 2; continue
        result2.append(line); i += 1

    return result2


def remove_runon_toc(lines: list[str]) -> list[str]:
    """
    Detect and remove magazine/book table-of-contents content at the top.
    TOC content: many short lines in a row, each line is a title/header,
    no prose paragraphs.
    """
    # Find if the first 40 lines look like a TOC
    first_40 = lines[:40]
    toc_line_count = 0
    for line in first_40:
        s = line.strip()
        if not s:
            continue
        # Short lines (< 70 chars), mostly title-case or all caps, no sentence structure
        words = s.split()
        if 2 <= len(words) <= 10 and not s.endswith('.') and not s.endswith(','):
            toc_line_count += 1

    toc_ratio = toc_line_count / max(len([l for l in first_40 if l.strip()]), 1)

    if toc_ratio > 0.6 and toc_line_count > 6:
        # This looks like a TOC at the start — find where prose begins
        # Prose = line with 20+ words or ends in period
        prose_start = 0
        for i, line in enumerate(lines):
            s = line.strip()
            words = s.split()
            if len(words) >= 15 or (s.endswith('.') and len(words) >= 8):
                prose_start = i
                break
        if prose_start > 5:
            return lines[prose_start:]

    return lines


def clean_stray_fragments(lines: list[str]) -> list[str]:
    """Remove lines that are clearly multi-column PDF artifacts (very short fragments)."""
    result = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip isolated 1-3 word fragments that aren't headings
        if stripped and len(stripped.split()) <= 2 and not stripped.startswith('#'):
            # If surrounded by blank lines and looks like a fragment
            prev_blank = (i == 0) or (lines[i - 1].strip() == "")
            next_blank = (i == len(lines) - 1) or (lines[i + 1].strip() == "")
            # Check if it ends mid-word (no punctuation at all)
            if prev_blank and next_blank and not any(c in stripped for c in '.!?:;,\'"()'):
                # Skip isolated micro-fragments like "tive energy" or "r:a"
                if len(stripped) < 20 and not stripped[0].isupper():
                    continue
        result.append(line)
    return result


def strip_toc_block(lines: list[str]) -> list[str]:
    """
    Remove embedded Table of Contents blocks anywhere in the document.
    Detects a ## Table Of Contents heading followed by dot-leader or short-line entries,
    and removes the whole block until the next real section or blank+prose start.
    """
    result = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        # Detect TOC heading
        is_toc_heading = re.match(
            r'^#{1,3}\s*(Table\s+[Oo]f\s+Contents|TABLE\s+OF\s+CONTENTS|Contents|LIST\s+OF\s+(FIGURES|TABLES|ABBREVIATIONS))',
            stripped
        )
        if is_toc_heading:
            # Skip forward until we find a non-TOC line (real heading ## or long prose)
            i += 1
            while i < len(lines):
                s = lines[i].strip()
                # Stop if we hit a real ## heading (not list-like) or a long paragraph
                if s.startswith('## ') or s.startswith('### '):
                    break
                # Stop if line is a long prose line (15+ words, ends with period)
                words = s.split()
                if len(words) >= 15 and s.endswith('.'):
                    break
                i += 1
            continue  # don't add the TOC heading or its entries
        result.append(lines[i])
        i += 1
    return result


def strip_statistical_output(lines: list[str]) -> list[str]:
    """
    Remove raw SPSS/statistical command output sections.
    Detects blocks of SPSS syntax commands and statistical table output
    (lines starting with /, UNIANOVA, GLM, /WSFACTOR, /CRITERIA, etc.)
    and removes them.
    Also removes large appendix sections that are pure statistical data.
    """
    result = []
    i = 0
    n = len(lines)

    # SPSS command patterns
    spss_cmd_re = re.compile(
        r'^(/[A-Z]|UNIANOVA\b|GLM\b|ONEWAY\b|MANOVA\b|ANOVA\b\s|/WSFACTOR|/WSDESIGN|/DESIGN|/PLOT|Syntax\s+GLM|Syntax\s+UNIANOVA)',
        re.IGNORECASE
    )
    # Statistical table content patterns (standalone numbers, factor labels)
    stat_table_re = re.compile(
        r'^(\d+\.\d+\s+\d+\.\d+|\d+\s+\d+\s+\d+|[A-Za-z]+\s+\d+\s+\d+|N\s+\d+$|Sig\.\s|Std\.\s|Mean\s+\d)',
    )

    while i < n:
        stripped = lines[i].strip()

        # Detect SPSS command block start
        if spss_cmd_re.match(stripped):
            # Skip this and following lines until we find real prose again
            skip_start = i
            while i < n:
                s = lines[i].strip()
                # Real prose: starts a new ## heading or is a long sentence
                if s.startswith('## ') or s.startswith('### '):
                    break
                words = s.split()
                if len(words) >= 12 and not spss_cmd_re.match(s) and not stat_table_re.match(s):
                    # Check it's not numbers-heavy
                    alpha_ratio = sum(1 for c in s if c.isalpha()) / max(len(s), 1)
                    if alpha_ratio > 0.5:
                        break
                i += 1
            continue

        result.append(lines[i])
        i += 1

    return result


def remove_repeated_headers(lines: list[str], title: str) -> list[str]:
    """Remove lines that repeat the document title (common in page headers)."""
    result = []
    title_words = set(title.lower().split()[:4])
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            result.append(line)
            continue
        # Check if this line substantially matches the title
        line_words = set(stripped.lower().split())
        if len(line_words) >= 3 and len(title_words & line_words) >= 3:
            overlap = len(title_words & line_words) / max(len(title_words), 1)
            if overlap > 0.6 and len(stripped) < 120:
                continue  # skip this repeated title line
        result.append(line)
    return result


def normalize_whitespace(lines: list[str]) -> list[str]:
    """Ensure no more than 2 consecutive blank lines."""
    result = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)
    # Remove leading/trailing blank lines
    while result and result[0].strip() == "":
        result.pop(0)
    while result and result[-1].strip() == "":
        result.pop()
    return result


def process_article(md_path: Path) -> bool:
    """Process a single article markdown file. Returns True if modified."""
    text = md_path.read_text(encoding="utf-8")

    # Split frontmatter from content
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = "---" + parts[1] + "---\n"
            content = parts[2].lstrip("\n")
        else:
            frontmatter = ""
            content = text
    else:
        frontmatter = ""
        content = text

    # Extract title from frontmatter for repeated-header detection
    title_match = re.search(r'^title:\s*"?([^"\n]+)"?', frontmatter, re.MULTILINE)
    doc_title = title_match.group(1) if title_match else ""

    original_content = content

    # Step 0: Strip PDF CID font encoding artifacts — (cid:N) tokens from
    # PDFs with embedded custom fonts that weren't mapped to Unicode.
    # First remove lines that are purely CID codes (table-of-contents garbage),
    # then strip inline CID tokens from mixed lines.
    lines_raw = content.split("\n")
    lines_clean = []
    for ln in lines_raw:
        # Drop lines that are >50% CID tokens (pure garbage)
        cid_count = len(re.findall(r'\(cid:\d+\)', ln))
        word_count = len(ln.split())
        if cid_count > 0 and word_count > 0 and cid_count / word_count > 0.5:
            continue
        # Strip inline CID tokens from otherwise readable lines
        ln = re.sub(r'\(cid:\d+\)\s*', '', ln).strip()
        lines_clean.append(ln)
    content = "\n".join(lines_clean)

    # Split into lines
    lines = content.split("\n")

    # Step 1: Strip boilerplate lines
    lines = clean_boilerplate(lines)

    # Step 2: Remove front matter (academic papers)
    lines, front_note = strip_front_matter(lines)

    # Step 3: Remove TOC blocks at start (magazines)
    lines = remove_runon_toc(lines)

    # Step 4: Fix PDF hyphenation
    lines = fix_paragraph_breaks(lines)

    # Step 5: Convert headings
    lines = convert_headings(lines)

    # Step 6: Strip embedded TOC sections (dissertation chapter lists, figures lists)
    lines = strip_toc_block(lines)

    # Step 7: Strip raw SPSS/statistical command output
    lines = strip_statistical_output(lines)

    # Step 8: Remove stray fragments
    lines = clean_stray_fragments(lines)

    # Step 9: Remove repeated title lines
    if doc_title:
        lines = remove_repeated_headers(lines, doc_title)

    # Step 10: Normalize whitespace
    lines = normalize_whitespace(lines)

    # Reassemble
    new_content = front_note + "\n".join(lines)

    if new_content.strip() != original_content.strip():
        md_path.write_text(frontmatter + "\n" + new_content + "\n", encoding="utf-8")
        return True

    return False


def main():
    md_files = sorted(ARTICLES_DIR.glob("*.md"))
    print(f"Processing {len(md_files)} article files...\n")

    modified = 0
    for md_file in md_files:
        changed = process_article(md_file)
        status = "✓ reformatted" if changed else "· unchanged"
        print(f"  {status}  {md_file.name}")
        if changed:
            modified += 1

    print(f"\n✅ Done — {modified}/{len(md_files)} articles reformatted")


if __name__ == "__main__":
    main()
