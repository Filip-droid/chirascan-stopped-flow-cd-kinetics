# src/views/icons.py
"""Icons of every button, menu entry, tab and toolbar action, drawn here with
QPainter (no image files to bundle or lose; they stay sharp at any scale).

Each icon is drawn in a 32 x 32 coordinate system and rendered at 16, 20, 24,
32 and 48 px. get(name) returns a cached QIcon; unknown names give an empty
icon rather than an error."""

import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen,
                         QPixmap, QPolygonF)

from src.modules.utils.resource_path import resource_path

BLUE = QColor("#1F5FA8")
LIGHT_BLUE = QColor("#9DB7DD")
GREEN = QColor("#2E7D32")
LIGHT_GREEN = QColor("#A5D6A7")
RED = QColor("#C62828")
ORANGE = QColor("#F57C00")
YELLOW = QColor("#F9C74F")
DARK = QColor("#37474F")
GREY = QColor("#78909C")
WHITE = QColor("#FFFFFF")
PURPLE = QColor("#6A1B9A")

_SIZES = (16, 20, 24, 32, 48)
_cache = {}


def _pen(color, width=2.0, cap=Qt.RoundCap):
    p = QPen(QColor(color), width)
    p.setCapStyle(cap)
    p.setJoinStyle(Qt.RoundJoin)
    return p


def _icon(draw):
    icon = QIcon()
    for size in _SIZES:
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.scale(size / 32.0, size / 32.0)
        draw(p)
        p.end()
        icon.addPixmap(pix)
    return icon


# ---------------------------------------------------------------- building blocks
def _document(p, fill=WHITE, edge=GREY, x=6, y=3, w=20, h=26):
    fold = 6
    path = QPainterPath(QPointF(x, y))
    path.lineTo(x + w - fold, y)
    path.lineTo(x + w, y + fold)
    path.lineTo(x + w, y + h)
    path.lineTo(x, y + h)
    path.closeSubpath()
    p.setPen(_pen(edge, 1.5))
    p.setBrush(fill)
    p.drawPath(path)
    p.drawLine(QPointF(x + w - fold, y), QPointF(x + w - fold, y + fold))
    p.drawLine(QPointF(x + w - fold, y + fold), QPointF(x + w, y + fold))


def _badge_plus(p, color=GREEN, cx=24, cy=24, r=7):
    p.setPen(Qt.NoPen)
    p.setBrush(color)
    p.drawEllipse(QPointF(cx, cy), r, r)
    p.setPen(_pen(WHITE, 2.2))
    p.drawLine(QPointF(cx - r * 0.55, cy), QPointF(cx + r * 0.55, cy))
    p.drawLine(QPointF(cx, cy - r * 0.55), QPointF(cx, cy + r * 0.55))


def _badge_minus(p, color=RED, cx=24, cy=24, r=7):
    p.setPen(Qt.NoPen)
    p.setBrush(color)
    p.drawEllipse(QPointF(cx, cy), r, r)
    p.setPen(_pen(WHITE, 2.2))
    p.drawLine(QPointF(cx - r * 0.55, cy), QPointF(cx + r * 0.55, cy))


def _folder(p, color=YELLOW):
    p.setPen(_pen(QColor("#C79A1E"), 1.4))
    p.setBrush(color.darker(110))
    back = QPainterPath(QPointF(3, 8))
    back.lineTo(12, 8)
    back.lineTo(14, 11)
    back.lineTo(28, 11)
    back.lineTo(28, 26)
    back.lineTo(3, 26)
    back.closeSubpath()
    p.drawPath(back)
    p.setBrush(color)
    front = QPolygonF([QPointF(3, 26), QPointF(7, 14), QPointF(31, 14), QPointF(28, 26)])
    p.drawPolygon(front)


def _axes(p, color=DARK):
    p.setPen(_pen(color, 1.8))
    p.drawLine(QPointF(5, 4), QPointF(5, 27))
    p.drawLine(QPointF(5, 27), QPointF(29, 27))


def _rise_path(x0=6, x1=28, y0=25, y1=7, k=4.0):
    path = QPainterPath()
    for i in range(41):
        t = i / 40
        x = x0 + (x1 - x0) * t
        y = y0 - (y0 - y1) * (1 - math.exp(-k * t))
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    return path


def _text(p, rect, text, color, size=12, bold=True, family="Segoe UI"):
    f = QFont(family)
    f.setPixelSize(size)
    f.setBold(bold)
    p.setFont(f)
    p.setPen(QColor(color))
    p.drawText(QRectF(*rect), Qt.AlignCenter, text)


# ---------------------------------------------------------------- the icons
def _d_open_folder(p):
    _folder(p)


def _d_add_files(p):
    _document(p, x=4, y=2, w=19, h=25)
    p.setPen(_pen(LIGHT_BLUE, 1.5))
    for y in (11, 15, 19):
        p.drawLine(QPointF(8, y), QPointF(18, y))
    _badge_plus(p)


def _d_remove(p):
    _document(p, x=4, y=2, w=19, h=25)
    _badge_minus(p)


def _d_clear(p):
    p.setPen(_pen(GREY, 1.5))
    p.setBrush(QColor("#ECEFF1"))
    p.drawRoundedRect(QRectF(5, 9, 22, 20), 2, 2)
    p.drawLine(QPointF(3, 9), QPointF(29, 9))
    p.drawRoundedRect(QRectF(12, 4, 8, 5), 1, 1)
    p.setPen(_pen(RED, 2.2))
    p.drawLine(QPointF(11, 14), QPointF(21, 24))
    p.drawLine(QPointF(21, 14), QPointF(11, 24))


def _d_save(p):
    p.setPen(_pen(QColor("#0D3C73"), 1.5))
    p.setBrush(BLUE)
    path = QPainterPath(QPointF(4, 4))
    path.lineTo(24, 4)
    path.lineTo(28, 8)
    path.lineTo(28, 28)
    path.lineTo(4, 28)
    path.closeSubpath()
    p.drawPath(path)
    p.setBrush(WHITE)
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(9, 4, 13, 8))
    p.setBrush(QColor("#E3F2FD"))
    p.drawRect(QRectF(8, 17, 16, 11))
    p.setBrush(BLUE)
    p.drawRect(QRectF(17, 5.5, 3, 5))


def _d_save_as(p):
    _d_save(p)
    p.setPen(_pen(ORANGE, 2.6))
    p.drawLine(QPointF(17, 27), QPointF(29, 15))
    p.setPen(_pen(DARK, 1.2))
    p.drawLine(QPointF(16, 29), QPointF(17.5, 26))


def _d_open_project(p):
    _folder(p)
    p.setPen(Qt.NoPen)
    p.setBrush(BLUE)
    p.drawEllipse(QPointF(19, 20), 4.5, 4.5)
    p.setPen(_pen(WHITE, 1.6))
    p.drawLine(QPointF(19, 17.5), QPointF(19, 22.5))
    p.drawLine(QPointF(16.5, 20), QPointF(21.5, 20))


def _d_excel(p):
    p.setPen(_pen(QColor("#1B5E20"), 1.4))
    p.setBrush(QColor("#E8F5E9"))
    p.drawRect(QRectF(10, 4, 19, 24))
    p.setPen(_pen(QColor("#81C784"), 1.2))
    for y in (10, 16, 22):
        p.drawLine(QPointF(19, y), QPointF(29, y))
    p.drawLine(QPointF(19, 4), QPointF(19, 28))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#1D6F42"))
    p.drawRoundedRect(QRectF(2, 8, 16, 16), 2, 2)
    _text(p, (2, 8, 16, 16), "X", WHITE, 13)


def _d_csv(p):
    _document(p)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#00897B"))
    p.drawRoundedRect(QRectF(2, 15, 22, 11), 2, 2)
    _text(p, (2, 15, 22, 11), "CSV", WHITE, 8)


def _d_image(p):
    p.setPen(_pen(GREY, 1.5))
    p.setBrush(QColor("#E3F2FD"))
    p.drawRoundedRect(QRectF(3, 6, 26, 21), 2, 2)
    p.setPen(Qt.NoPen)
    p.setBrush(YELLOW)
    p.drawEllipse(QPointF(10, 12), 3, 3)
    p.setBrush(GREEN)
    p.drawPolygon(QPolygonF([QPointF(4, 26), QPointF(13, 16), QPointF(19, 22), QPointF(23, 18), QPointF(28, 26)]))


def _d_copy(p):
    for dx, fill in ((0, QColor("#ECEFF1")), (6, WHITE)):
        p.setPen(_pen(GREY, 1.5))
        p.setBrush(fill)
        p.drawRoundedRect(QRectF(5 + dx, 4 + dx, 16, 20), 2, 2)
    p.setPen(_pen(LIGHT_BLUE, 1.4))
    for y in (16, 20, 24):
        p.drawLine(QPointF(14, y), QPointF(23, y))


def _d_run(p):
    p.setPen(Qt.NoPen)
    p.setBrush(GREEN)
    p.drawPolygon(QPolygonF([QPointF(8, 5), QPointF(27, 16), QPointF(8, 27)]))


def _d_run_all(p):
    p.setPen(Qt.NoPen)
    p.setBrush(GREEN.lighter(140))
    p.drawPolygon(QPolygonF([QPointF(3, 6), QPointF(17, 16), QPointF(3, 26)]))
    p.setBrush(GREEN)
    p.drawPolygon(QPolygonF([QPointF(13, 6), QPointF(29, 16), QPointF(13, 26)]))


def _d_stop(p):
    p.setPen(Qt.NoPen)
    p.setBrush(RED)
    p.drawRoundedRect(QRectF(7, 7, 18, 18), 3, 3)


def _d_fit(p):
    _axes(p)
    p.setPen(Qt.NoPen)
    p.setBrush(BLUE)
    for t in (0.05, 0.15, 0.27, 0.4, 0.55, 0.72, 0.9):
        x = 6 + 22 * t
        y = 25 - 18 * (1 - math.exp(-4 * t)) + (1.5 if int(t * 20) % 2 else -1.5)
        p.drawEllipse(QPointF(x, y), 1.6, 1.6)
    p.setPen(_pen(RED, 2.0))
    p.setBrush(Qt.NoBrush)
    p.drawPath(_rise_path())


def _d_raw(p):
    _axes(p)
    p.setBrush(Qt.NoBrush)
    for color, off in ((QColor("#90CAF9"), 3), (QColor("#64B5F6"), 0), (BLUE, -3)):
        path = QPainterPath()
        for i in range(25):
            t = i / 24
            x = 6 + 22 * t
            y = 24 - 14 * (1 - math.exp(-4 * t)) + off + (1.4 if i % 2 else -1.4)
            path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
        p.setPen(_pen(color, 1.2))
        p.drawPath(path)


def _d_average(p):
    _axes(p)
    p.setBrush(Qt.NoBrush)
    for off in (4, -4):
        path = QPainterPath()
        for i in range(25):
            t = i / 24
            path.moveTo(6, 24 + off) if i == 0 else path.lineTo(6 + 22 * t, 24 - 14 * (1 - math.exp(-4 * t)) + off)
        p.setPen(_pen(LIGHT_BLUE, 1.2))
        p.drawPath(path)
    p.setPen(_pen(BLUE, 2.4))
    p.drawPath(_rise_path(6, 28, 24, 10))


def _d_trim(p):
    _axes(p)
    p.setPen(_pen(BLUE, 1.6))
    p.setBrush(Qt.NoBrush)
    p.drawPath(_rise_path(10, 28, 23, 8))
    p.setPen(_pen(RED, 1.8, Qt.FlatCap))
    p.drawLine(QPointF(10, 3), QPointF(10, 27))
    p.setPen(Qt.NoPen)
    p.setBrush(RED)
    p.drawEllipse(QPointF(7.5, 22), 1.6, 1.6)
    p.drawEllipse(QPointF(7.5, 16), 1.6, 1.6)


def _d_convert(p):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#EDE7F6"))
    p.drawRoundedRect(QRectF(1, 4, 30, 24), 5, 5)
    _text(p, (1, 4, 30, 24), "Δε", PURPLE, 17, family="Times New Roman")


def _d_compare(p):
    _axes(p)
    p.setBrush(Qt.NoBrush)
    p.setPen(_pen(RED, 2.0))
    p.drawPath(_rise_path(6, 28, 25, 7, 4.0))
    p.setPen(_pen(GREEN, 2.0, Qt.FlatCap))
    pen = p.pen()
    pen.setDashPattern([2, 2])
    p.setPen(pen)
    p.drawPath(_rise_path(6, 28, 25, 11, 1.8))


def _d_ftest(p):
    p.setPen(_pen(DARK, 1.8))
    p.drawLine(QPointF(16, 5), QPointF(16, 27))
    p.drawLine(QPointF(9, 27), QPointF(23, 27))
    p.drawLine(QPointF(5, 9), QPointF(27, 7))
    p.setBrush(QColor("#FFE0B2"))
    p.setPen(_pen(ORANGE, 1.4))
    for cx, cy in ((7, 9.5), (25, 7.5)):
        path = QPainterPath(QPointF(cx - 5, cy + 6))
        path.lineTo(cx + 5, cy + 6)
        path.arcTo(QRectF(cx - 5, cy + 1, 10, 10), 0, -180)
        p.drawLine(QPointF(cx, cy), QPointF(cx - 4.5, cy + 6))
        p.drawLine(QPointF(cx, cy), QPointF(cx + 4.5, cy + 6))
        p.drawPath(path)
    _text(p, (11, 12, 10, 10), "F", BLUE, 10)


def _d_reset(p):
    p.setPen(_pen(BLUE, 2.6))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(6, 6, 20, 20), 100 * 16, 280 * 16)
    p.setPen(Qt.NoPen)
    p.setBrush(BLUE)
    p.drawPolygon(QPolygonF([QPointF(11, 2), QPointF(19, 6), QPointF(12, 11)]))


def _d_refresh(p):
    p.setPen(_pen(GREEN, 2.6))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(6, 6, 20, 20), 30 * 16, 300 * 16)
    p.setPen(Qt.NoPen)
    p.setBrush(GREEN)
    p.drawPolygon(QPolygonF([QPointF(27, 3), QPointF(28, 12), QPointF(20, 10)]))


def _d_help(p):
    p.setPen(Qt.NoPen)
    p.setBrush(ORANGE)
    p.drawEllipse(QRectF(3, 3, 26, 26))
    _text(p, (3, 3, 26, 26), "?", WHITE, 19)


def _d_quick_help(p):
    p.setPen(Qt.NoPen)
    p.setBrush(ORANGE)
    p.drawRoundedRect(QRectF(4, 4, 24, 24), 5, 5)
    _text(p, (4, 4, 24, 24), "?", WHITE, 17)


def _d_search(p):
    p.setPen(_pen(BLUE, 3.0))
    p.setBrush(QColor("#E3F2FD"))
    p.drawEllipse(QRectF(4, 4, 16, 16))
    p.setPen(_pen(DARK, 4.0))
    p.drawLine(QPointF(18.5, 18.5), QPointF(27, 27))


def _d_book(p):
    p.setPen(_pen(QColor("#0D3C73"), 1.4))
    p.setBrush(BLUE)
    p.drawRoundedRect(QRectF(6, 3, 21, 26), 2, 2)
    p.setBrush(WHITE)
    p.drawRect(QRectF(9, 24, 18, 4))
    p.setPen(_pen(WHITE, 1.8))
    p.drawLine(QPointF(12, 9), QPointF(23, 9))
    p.drawLine(QPointF(12, 13), QPointF(20, 13))


def _d_quick_start(p):
    p.setPen(Qt.NoPen)
    p.setBrush(YELLOW)
    p.drawPolygon(QPolygonF([QPointF(18, 2), QPointF(7, 18), QPointF(15, 18), QPointF(12, 30),
                             QPointF(25, 12), QPointF(17, 12), QPointF(21, 2)]))
    p.setPen(_pen(QColor("#C79A1E"), 1.2))
    p.setBrush(Qt.NoBrush)
    p.drawPolygon(QPolygonF([QPointF(18, 2), QPointF(7, 18), QPointF(15, 18), QPointF(12, 30),
                             QPointF(25, 12), QPointF(17, 12), QPointF(21, 2)]))


def _d_info(p):
    p.setPen(Qt.NoPen)
    p.setBrush(BLUE)
    p.drawEllipse(QRectF(3, 3, 26, 26))
    _text(p, (3, 4, 26, 26), "i", WHITE, 19, family="Georgia")


def _d_license(p):
    _document(p)
    p.setPen(_pen(LIGHT_BLUE, 1.4))
    for y in (10, 14):
        p.drawLine(QPointF(9, y), QPointF(20, y))
    p.setPen(Qt.NoPen)
    p.setBrush(RED)
    p.drawEllipse(QPointF(20, 22), 5, 5)
    p.drawPolygon(QPolygonF([QPointF(17, 25), QPointF(16, 31), QPointF(19, 29), QPointF(20, 31),
                             QPointF(21, 26)]))


def _d_install(p):
    p.setPen(_pen(QColor("#8D6E63"), 1.4))
    p.setBrush(QColor("#D7B98E"))
    p.drawRect(QRectF(5, 15, 22, 13))
    p.drawLine(QPointF(5, 15), QPointF(9, 10))
    p.drawLine(QPointF(27, 15), QPointF(23, 10))
    p.setPen(Qt.NoPen)
    p.setBrush(GREEN)
    p.drawRect(QRectF(13.5, 2, 5, 8))
    p.drawPolygon(QPolygonF([QPointF(9, 10), QPointF(23, 10), QPointF(16, 18)]))


def _d_exit(p):
    p.setPen(_pen(RED, 3.0))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(5, 6, 22, 22), 120 * 16, 300 * 16)
    p.drawLine(QPointF(16, 3), QPointF(16, 16))


def _d_report(p):
    p.setPen(_pen(GREY, 1.4))
    p.setBrush(QColor("#FFFDE7"))
    p.drawRoundedRect(QRectF(5, 4, 22, 25), 2, 2)
    p.setPen(_pen(DARK, 1.4))
    for y in (10, 14, 18, 22):
        p.drawLine(QPointF(9, y), QPointF(23 - (y % 8), y))


def _d_table(p):
    p.setPen(_pen(QColor("#3B5B8C"), 1.4))
    p.setBrush(WHITE)
    p.drawRect(QRectF(3, 5, 26, 22))
    p.fillRect(QRectF(3.7, 5.7, 24.6, 6.3), QColor("#9DB7DD"))
    for y in (12, 19.5):
        p.drawLine(QPointF(3, y), QPointF(29, y))
    for x in (12, 20.5):
        p.drawLine(QPointF(x, 5), QPointF(x, 27))


def _d_flask(p):
    p.setPen(_pen(DARK, 1.5))
    path = QPainterPath(QPointF(12, 3))
    path.lineTo(20, 3)
    path.moveTo(13, 3)
    path.lineTo(13, 12)
    path.lineTo(5, 27)
    path.lineTo(27, 27)
    path.lineTo(19, 12)
    path.lineTo(19, 3)
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#4FC3F7"))
    p.drawPolygon(QPolygonF([QPointF(9, 19.5), QPointF(23, 19.5), QPointF(26.2, 26.2), QPointF(5.8, 26.2)]))
    p.setBrush(WHITE)
    p.drawEllipse(QPointF(13, 23), 1.5, 1.5)
    p.drawEllipse(QPointF(18, 22), 1, 1)


def _d_check_all(p):
    for y, checked in ((5, True), (17, True)):
        p.setPen(_pen(GREY, 1.4))
        p.setBrush(WHITE)
        p.drawRoundedRect(QRectF(4, y, 10, 10), 2, 2)
        if checked:
            p.setPen(_pen(GREEN, 2.2))
            p.drawPolyline(QPolygonF([QPointF(6, y + 5), QPointF(8.5, y + 8), QPointF(13, y + 2)]))
        p.setPen(_pen(DARK, 1.6))
        p.drawLine(QPointF(17, y + 5), QPointF(28, y + 5))


def _d_check_none(p):
    for y in (5, 17):
        p.setPen(_pen(GREY, 1.4))
        p.setBrush(WHITE)
        p.drawRoundedRect(QRectF(4, y, 10, 10), 2, 2)
        p.setPen(_pen(DARK, 1.6))
        p.drawLine(QPointF(17, y + 5), QPointF(28, y + 5))


def _d_settings(p):
    p.setPen(Qt.NoPen)
    p.setBrush(GREY)
    c = QPointF(16, 16)
    for i in range(8):
        a = i * math.pi / 4
        p.save()
        p.translate(c)
        p.rotate(math.degrees(a))
        p.drawRoundedRect(QRectF(-3, -14, 6, 8), 1, 1)
        p.restore()
    p.drawEllipse(c, 10, 10)
    p.setBrush(WHITE)
    p.drawEllipse(c, 4, 4)


def _d_data(p):
    p.setPen(_pen(DARK, 1.2))
    p.setBrush(QColor("#E3F2FD"))
    for y in (22, 14, 6):
        p.drawEllipse(QRectF(5, y, 22, 7))
        if y != 6:
            p.drawRect(QRectF(5, y - 4, 22, 8))
    p.setBrush(LIGHT_BLUE)
    p.drawEllipse(QRectF(5, 4, 22, 7))


def _d_log_x(p):
    _axes(p)
    _text(p, (6, 4, 24, 16), "log", BLUE, 10)
    p.setPen(_pen(GREY, 1.0))
    for x in (8, 11, 13, 14.5, 18, 22, 25, 27):
        p.drawLine(QPointF(x, 25), QPointF(x, 27))


def _d_zoom_fit(p):
    p.setPen(_pen(DARK, 1.8))
    for (x, y), (dx, dy) in (((4, 4), (1, 1)), ((28, 4), (-1, 1)), ((4, 28), (1, -1)), ((28, 28), (-1, -1))):
        p.drawLine(QPointF(x, y), QPointF(x + 6 * dx, y))
        p.drawLine(QPointF(x, y), QPointF(x, y + 6 * dy))
    p.setPen(_pen(BLUE, 1.8))
    p.setBrush(Qt.NoBrush)
    p.drawPath(_rise_path(9, 23, 22, 10))


def _d_whats_new(p):
    p.setPen(Qt.NoPen)
    p.setBrush(ORANGE)
    pts = []
    for i in range(10):
        r = 13 if i % 2 == 0 else 6
        a = -math.pi / 2 + i * math.pi / 5
        pts.append(QPointF(16 + r * math.cos(a), 17 + r * math.sin(a)))
    p.drawPolygon(QPolygonF(pts))


def _d_log_file(p):
    _document(p)
    p.setPen(_pen(DARK, 1.2))
    for y in (11, 15, 19, 23):
        p.drawLine(QPointF(9, y), QPointF(11, y))
        p.drawLine(QPointF(13, y), QPointF(21, y))


def _spectrum_path(x0=6, x1=28, y_zero=17, a1=9, a2=5):
    """A CD spectrum: a positive band, then a smaller negative one."""
    path = QPainterPath()
    for i in range(41):
        t = i / 40
        x = x0 + (x1 - x0) * t
        y = y_zero - a1 * math.exp(-((t - 0.38) / 0.16) ** 2) + a2 * math.exp(-((t - 0.78) / 0.12) ** 2)
        path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
    return path


def _d_spectrum(p):
    _axes(p)
    p.setPen(_pen(GREY, 1.0, Qt.FlatCap))
    p.drawLine(QPointF(6, 17), QPointF(29, 17))
    p.setBrush(Qt.NoBrush)
    p.setPen(_pen(LIGHT_BLUE, 1.4))
    p.drawPath(_spectrum_path(a1=6, a2=3))
    p.setPen(_pen(PURPLE, 2.2))
    p.drawPath(_spectrum_path())


def _d_dsx(p):
    _document(p)
    p.setPen(Qt.NoPen)
    p.setBrush(PURPLE)
    p.drawRoundedRect(QRectF(2, 15, 22, 11), 2, 2)
    _text(p, (2, 15, 22, 11), "DSX", WHITE, 8)


_DRAW = {
    "open_folder": _d_open_folder, "add_files": _d_add_files, "remove": _d_remove, "clear": _d_clear,
    "save": _d_save, "save_as": _d_save_as, "open_project": _d_open_project, "excel": _d_excel,
    "csv": _d_csv, "image": _d_image, "copy": _d_copy, "run": _d_run, "run_all": _d_run_all,
    "stop": _d_stop, "fit": _d_fit, "raw": _d_raw, "average": _d_average, "trim": _d_trim,
    "convert": _d_convert, "compare": _d_compare, "ftest": _d_ftest, "reset": _d_reset,
    "refresh": _d_refresh, "help": _d_help, "quick_help": _d_quick_help, "search": _d_search,
    "book": _d_book, "quick_start": _d_quick_start, "info": _d_info, "license": _d_license,
    "install": _d_install, "exit": _d_exit, "report": _d_report, "table": _d_table, "flask": _d_flask,
    "check_all": _d_check_all, "check_none": _d_check_none, "settings": _d_settings, "data": _d_data,
    "log_x": _d_log_x, "zoom_fit": _d_zoom_fit, "whats_new": _d_whats_new, "log_file": _d_log_file,
    "spectrum": _d_spectrum, "dsx": _d_dsx,
}

NAMES = tuple(_DRAW)


def get(name):
    """The QIcon `name` (cached)."""
    if name not in _cache:
        if name == "app":
            _cache[name] = app_icon()
        else:
            draw = _DRAW.get(name)
            _cache[name] = _icon(draw) if draw else QIcon()
    return _cache[name]


def app_icon():
    """The program's own icon (resources/icons/app_icon.ico / .png), or a drawn fallback."""
    for fname in ("app_icon.ico", "app_icon.png"):
        icon = QIcon(resource_path("icons", fname))
        if not icon.isNull():
            return icon
    return _icon(_d_fit)


def help_button(tooltip, parent=None):
    """The small orange '?' of the quick (context) help."""
    from PyQt5.QtWidgets import QToolButton
    btn = QToolButton(parent)
    btn.setText("?")
    btn.setFixedSize(22, 22)
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(
        "QToolButton { background-color:#F57C00; color:white; font-weight:bold; border:none; "
        "border-radius:4px; font-size:13px; }"
        "QToolButton:hover { background-color:#E65100; }"
        "QToolButton:pressed { background-color:#BF360C; }")
    return btn


def gradient_banner(width, height, c1="#1F5FA8", c2="#4FC3F7"):
    """A QBrush gradient for headers."""
    g = QLinearGradient(0, 0, width, height)
    g.setColorAt(0, QColor(c1))
    g.setColorAt(1, QColor(c2))
    return QBrush(g)
