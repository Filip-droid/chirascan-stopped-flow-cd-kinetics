# tests/test_help_and_icons.py
"""Help pages render, cross-links point to existing pages and anchors, every
quick help links to an existing section, the search finds things, every icon
draws."""

import os
import re

from src.help import help_pages, help_search
from src.help.quick_help import QUICK_HELP, STEP_HELP


def _ids(key):
    return set(re.findall(r'\bid="([^"]+)"', help_pages.page_content(key)))


def test_pages_render(tmp_path, monkeypatch):
    monkeypatch.setattr(help_pages, "pages_dir", lambda: str(tmp_path))
    help_pages.write_all_pages()
    for key in help_pages.REGISTRY:
        assert (tmp_path / f"{key}.html").stat().st_size > 1000


def test_links_resolve():
    for key in help_pages.REGISTRY:
        for target, anchor in re.findall(r'help://([a-z_]+)(?:#([a-z0-9-]+))?', help_pages.page_content(key)):
            assert target in help_pages.REGISTRY, (key, target)
            if anchor:
                assert anchor in _ids(target), (key, target, anchor)
        for anchor in re.findall(r'href="#([^"]+)"', help_pages.page_content(key)):
            assert anchor in _ids(key), (key, anchor)


def test_quick_help_targets():
    for key, (title, (page, anchor), body) in QUICK_HELP.items():
        assert page in help_pages.REGISTRY
        assert anchor in _ids(page), (key, page, anchor)
    for k in STEP_HELP:
        assert k in QUICK_HELP


def test_search():
    hits = help_search.search("half-lives")
    assert hits and any(h["key"] == "models" for h in hits)
    assert help_search.search("multi start")
    assert help_search.search("") == []


def test_icons_draw():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])  # noqa: F841
    from src.views import icons
    for name in icons.NAMES:
        assert not icons.get(name).isNull(), name
    assert not icons.get("app").isNull()


def test_quick_help_keys_used_in_views():
    root = os.path.join(os.path.dirname(__file__), "..", "src", "views", "panels")
    used = set()
    for f in os.listdir(root):
        if f.endswith(".py"):
            used |= set(re.findall(r'help_group\([^,]+,\s*"([a-z_]+)"', open(os.path.join(root, f), encoding="utf-8").read()))
    assert used <= set(QUICK_HELP), used - set(QUICK_HELP)
