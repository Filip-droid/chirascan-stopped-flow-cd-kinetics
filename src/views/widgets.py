# src/views/widgets.py
"""Small reusable widgets and helpers of the views."""

import math

from PyQt5.QtWidgets import QDoubleSpinBox, QGroupBox, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from src.views import icons


def button(text, icon=None, tooltip=None, primary=False):
    b = QPushButton(text)
    if icon:
        b.setIcon(icons.get(icon))
    if tooltip:
        b.setToolTip(tooltip)
    if primary:
        b.setProperty("primary", True)
    b.setAutoDefault(False)
    return b


class _HelpGroupBox(QGroupBox):
    """Group box that keeps its "?" button in the top-right corner, on the frame line."""

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, "help_button", None) is not None:
            self.help_button.move(self.width() - self.help_button.width() - 8, 1)
            self.help_button.raise_()


def help_group(title, help_key, tooltip=None):
    """A group box with the orange quick-help "?" in its top-right corner.
    Returns (group box, its content layout). The "?" carries the property
    helpKey; the help controller connects every such button at once."""
    box = _HelpGroupBox(title)
    content = QVBoxLayout(box)
    content.setContentsMargins(8, 10, 8, 8)
    content.setSpacing(6)
    q = icons.help_button(tooltip or f"Quick help: {title}", box)
    q.setFixedSize(20, 20)
    q.setProperty("helpKey", help_key)
    box.help_button = q
    return box, content


def hint(text):
    lab = QLabel(text)
    lab.setObjectName("hint")
    lab.setWordWrap(True)
    return lab


def dspin(minimum, maximum, decimals, step, value, suffix="", tooltip=None):
    s = QDoubleSpinBox()
    s.setRange(minimum, maximum)
    s.setDecimals(decimals)
    s.setSingleStep(step)
    s.setValue(value)
    s.setKeyboardTracking(False)
    if suffix:
        s.setSuffix(suffix)
    if tooltip:
        s.setToolTip(tooltip)
    s.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return s


def format_number(v, digits=6):
    """A float as text; ±inf as 'inf' / '-inf'."""
    if v is None:
        return ""
    v = float(v)
    if math.isinf(v):
        return "inf" if v > 0 else "-inf"
    if math.isnan(v):
        return "nan"
    return f"{v:.{digits}g}"


def parse_number(text):
    """Text -> float; accepts 'inf', '-inf', '∞', comma as decimal separator."""
    t = text.strip().replace(",", ".").replace("∞", "inf").lower()
    if t in ("", "none"):
        raise ValueError("empty value")
    return float(t)


def parse_list(text):
    """'1, 2; 3' or '1 2 3' -> [1.0, 2.0, 3.0]."""
    parts = [p for p in text.replace(";", " ").replace(",", " ").split() if p]
    return [parse_number(p) for p in parts]


class Separator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet("background:#CFD8DC;")
