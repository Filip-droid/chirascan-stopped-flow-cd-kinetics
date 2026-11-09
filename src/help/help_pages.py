# src/help/help_pages.py
"""The help "site": every topic is written to a real .html file and opened in
the user's own web browser (as in SpecAnalytiXBase: no embedded browser
engine for antivirus software to object to, perfect rendering and zoom).

All pages are written together (cross-links must exist before the browser
follows them), with a common style and a navigation bar. help://key#anchor
links in the page sources become ordinary relative links."""

import os
import re
import webbrowser

from src.help.pages import data_format, faq, models, quick_start, user_guide
from src.help.pages.misc_pages import installation, license, whats_new
from src.modules.utils.app_logger import app_data_dir, get_logger
from src.version import APP_NAME, APP_VERSION

logger = get_logger(__name__)

# key -> page module/class (order = order of the navigation bar). Imported
# explicitly, so PyInstaller bundles all of them.
REGISTRY = {
    "quick_start": quick_start,
    "user_guide": user_guide,
    "models": models,
    "data_format": data_format,
    "faq": faq,
    "whats_new": whats_new,
    "installation": installation,
    "license": license,
}

_HELP_LINK = re.compile(r'help://([a-zA-Z0-9_]+)')

CSS = """
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 15px; line-height: 1.55; color: #263238;
       margin: 0; background: #F4F6F9; }
header { background: linear-gradient(90deg, #1F5FA8, #4FC3F7); color: white; padding: 10px 24px; }
header .app { font-weight: bold; font-size: 18px; }
header .ver { opacity: .85; margin-left: 8px; font-size: 13px; }
nav { background: #FFFFFF; border-bottom: 1px solid #CFD8DC; padding: 6px 18px; position: sticky; top: 0; }
nav a { margin-right: 14px; text-decoration: none; color: #1F5FA8; font-size: 14px; white-space: nowrap; }
nav a.current { font-weight: bold; color: #0D3C73; border-bottom: 2px solid #F57C00; }
main { max-width: 960px; margin: 18px auto; background: white; padding: 10px 34px 30px 34px;
       border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
h1 { color: #1F5FA8; border-bottom: 2px solid #E3F2FD; padding-bottom: 6px; }
h2 { color: #1F5FA8; margin-top: 30px; }
h3 { color: #37474F; }
.lead { font-size: 16px; color: #455A64; }
code, pre { font-family: Consolas, "Courier New", monospace; background: #F1F4F8; border-radius: 3px; }
code { padding: 1px 4px; }
pre { padding: 10px; overflow-x: auto; }
table { border-collapse: collapse; margin: 10px 0; }
th, td { border: 1px solid #CFD8DC; padding: 5px 10px; text-align: left; vertical-align: top; }
th { background: #E8EDF3; }
.eq { font-family: "Cambria Math", "Times New Roman", serif; font-size: 17px; background: #F3E5F5;
      border-left: 4px solid #6A1B9A; padding: 8px 14px; margin: 10px 0; color: #4A148C; }
.note { background: #FFF3E0; border-left: 4px solid #F57C00; padding: 8px 12px; }
.toc { background: #F1F8E9; border: 1px solid #C5E1A5; border-radius: 6px; padding: 8px 16px; }
.q { background: #F57C00; color: white; font-weight: bold; border-radius: 4px; padding: 0 6px; }
.old { color: #B71C1C; font-style: italic; }
.steps .step { display: flex; gap: 14px; align-items: flex-start; margin: 12px 0; }
.steps .num { flex: none; width: 34px; height: 34px; border-radius: 50%; background: #1F5FA8; color: white;
              font-weight: bold; font-size: 18px; text-align: center; line-height: 34px; }
.steps h3 { margin: 4px 0; }
:target { background: #FFF8E1; }
footer { text-align: center; color: #90A4AE; font-size: 12px; margin: 20px; }
"""


def pages_dir():
    return os.path.join(app_data_dir(), "help_pages")


def page_title(key):
    return REGISTRY[key].TITLE


def page_content(key):
    return REGISTRY[key].content()


def _rewrite_links(html):
    return _HELP_LINK.sub(lambda m: f"{m.group(1)}.html", html)


def render_page(key):
    current = ' class="current"'
    nav = " ".join(
        f'<a href="{k}.html"{current if k == key else ""}>{REGISTRY[k].TITLE}</a>'
        for k in REGISTRY)
    body = _rewrite_links(page_content(key))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{page_title(key)} – {APP_NAME} help</title>
<style>{CSS}</style></head>
<body>
<header><span class="app">{APP_NAME}</span><span class="ver">version {APP_VERSION} – help</span></header>
<nav>{nav}</nav>
<main>
{body}
</main>
<footer>{APP_NAME} {APP_VERSION} · press Ctrl+F to search this page, F1 in the program to search all pages</footer>
</body></html>"""


def write_all_pages():
    """Write every page; returns the folder."""
    folder = pages_dir()
    os.makedirs(folder, exist_ok=True)
    for key in REGISTRY:
        try:
            with open(os.path.join(folder, f"{key}.html"), "w", encoding="utf-8") as f:
                f.write(render_page(key))
        except Exception as exc:          # noqa: BLE001 - one broken page must not stop the others
            logger.warning("help: page %s not written: %s", key, exc)
    return folder


def page_url(key, anchor=None):
    """file:// URL of a page; with an anchor a small redirect page is used,
    because Windows drops the #fragment of file URLs passed to the browser."""
    folder = write_all_pages()
    path = os.path.join(folder, f"{key}.html")
    if not anchor:
        return "file:///" + path.replace("\\", "/").lstrip("/")
    stub = os.path.join(folder, "_goto.html")
    with open(stub, "w", encoding="utf-8") as f:
        f.write(f'<!DOCTYPE html><html><head><meta charset="utf-8">'
                f'<meta http-equiv="refresh" content="0; url={key}.html#{anchor}">'
                f'<script>location.replace("{key}.html#{anchor}");</script></head>'
                f'<body><a href="{key}.html#{anchor}">{page_title(key)}</a></body></html>')
    return "file:///" + stub.replace("\\", "/").lstrip("/")


def open_page(key, anchor=None):
    """Open a help page (at a section) in the default browser. Returns True on success."""
    if key not in REGISTRY:
        logger.warning("help: unknown page %s", key)
        return False
    try:
        url = page_url(key, anchor)
        logger.info("help: opening %s", url)
        return bool(webbrowser.open(url))
    except Exception as exc:              # noqa: BLE001
        logger.error("help: cannot open %s: %s", key, exc)
        return False
