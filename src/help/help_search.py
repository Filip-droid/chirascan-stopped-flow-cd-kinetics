# src/help/help_search.py
"""Help › Search the help (F1): find words in all help pages at once (the
browser's Ctrl+F searches only the open page). Every page is cut into its
sections (elements with an id); a section containing every typed word is a
hit - those whose heading or page title contains the words first. The quick
help texts are searched too."""

import html
import re

from src.help.help_pages import REGISTRY, page_content, page_title
from src.help.quick_help import QUICK_HELP

SKIPPED = {"license"}

_TAG = re.compile(r"<[^>]+>")
_ID = re.compile(r'<(h[1-6]|p|li|div|section|tr|td|span)\b[^>]*\bid="([^"]+)"[^>]*>', re.I)
_DROP = re.compile(r"<(script|style|svg)\b.*?</\1>", re.I | re.S)
_index = None


def _text(fragment):
    t = _TAG.sub(" ", _DROP.sub(" ", fragment))
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def _heading(tag, fragment):
    if tag.lower().startswith("h"):
        m = re.search(r"^(.*?)</%s>" % tag, fragment, re.I | re.S)
        if m:
            return _text(m.group(1))
    words = _text(fragment).split()
    return " ".join(words[:8]) + (" …" if len(words) > 8 else "")


def sections(content):
    """[(anchor, heading, text)] of a help page."""
    content = _DROP.sub(" ", content)
    marks = list(_ID.finditer(content))
    out = []
    first = marks[0].start() if marks else len(content)
    head = _text(content[:first])
    if head:
        out.append((None, "", head))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(content)
        fragment = content[m.end():end]
        text = _text(fragment)
        if text:
            out.append((m.group(2), _heading(m.group(1), fragment), text))
    return out


def build_index():
    """[(key, page title, anchor, heading, text)] of every page and quick help."""
    index = []
    for key in REGISTRY:
        if key in SKIPPED:
            continue
        try:
            title, content = page_title(key), page_content(key)
        except Exception:                   # noqa: BLE001
            continue
        for anchor, heading, text in sections(content):
            index.append((key, title, anchor, heading, text))
    for qkey, (qtitle, (page, anchor), body) in QUICK_HELP.items():
        index.append((page, "Quick help", anchor, qtitle, _text(body)))
    return index


def index():
    global _index
    if _index is None:
        _index = build_index()
    return _index


def _snippet(text, word, width=160):
    i = text.lower().find(word)
    if i < 0:
        return text[:width] + ("…" if len(text) > width else "")
    a = max(0, i - width // 3)
    b = min(len(text), a + width)
    return ("…" if a else "") + text[a:b] + ("…" if b < len(text) else "")


def search(query, entries=None, limit=80):
    """Sections containing every word of `query` (case ignored), best first:
    [{'key', 'title', 'anchor', 'heading', 'snippet'}]."""
    words = [w for w in re.split(r"[\s\-]+", query.lower().strip()) if w]
    if not words:
        return []
    found = []
    for n, (key, title, anchor, heading, text) in enumerate(entries if entries is not None else index()):
        low, h, t = (v.lower().replace("-", " ") for v in (text, heading, title))
        if not all(w in low or w in h or w in t for w in words):
            continue
        score = 0
        for w in words:
            score += 10 * (w in h) + 4 * (w in t) + min(low.count(w), 5)
        found.append((-score, n, {"key": key, "title": title, "anchor": anchor, "heading": heading,
                                  "snippet": _snippet(text, words[0])}))
    found.sort(key=lambda x: (x[0], x[1]))
    return [f for _, _, f in found[:limit]]
