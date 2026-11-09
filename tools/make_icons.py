"""Draws the program icon, the setup and uninstall icons and the installer
wizard images (Pillow). Run from the project root: python tools/make_icons.py"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
S = 1024


def gradient(size, c1, c2, diagonal=True):
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = ((x / w) + (y / h)) / 2 if diagonal else y / h
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return img


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def base_icon():
    bg = gradient((S, S), (13, 60, 115), (41, 182, 246)).convert("RGBA")
    icon = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    icon.paste(bg, (0, 0), rounded_mask((S, S), 200))
    d = ImageDraw.Draw(icon)
    # axes
    ax0, ay0, ax1, ay1 = 170, 150, 880, 850
    d.line([(ax0, ay0), (ax0, ay1), (ax1, ay1)], fill=(255, 255, 255, 235), width=34, joint="curve")
    # fitted curve
    pts = []
    for i in range(200):
        t = i / 199
        x = ax0 + 45 + (ax1 - ax0 - 80) * t
        y = ay1 - 60 - 560 * (1 - 0.55 * math.exp(-9 * t) - 0.45 * math.exp(-2.2 * t))
        pts.append((x, y))
    d.line(pts, fill=(255, 112, 67, 255), width=40, joint="curve")
    # noisy data points
    import random
    random.seed(3)
    for i in range(22):
        t = i / 21
        x = ax0 + 45 + (ax1 - ax0 - 80) * t
        y = ay1 - 60 - 560 * (1 - 0.55 * math.exp(-9 * t) - 0.45 * math.exp(-2.2 * t)) + random.uniform(-45, 45)
        r = 19
        d.ellipse([x - r, y - r, x + r, y + r], fill=(227, 242, 253, 255), outline=(13, 60, 115, 255), width=5)
    # stopwatch badge (stopped-flow)
    cx, cy, r = 690, 640, 135
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255), outline=(13, 60, 115, 255), width=26)
    d.rectangle([cx - 30, cy - r - 60, cx + 30, cy - r + 5], fill=(255, 255, 255, 255))
    d.line([(cx, cy), (cx, cy - 100)], fill=(13, 60, 115, 255), width=26)
    d.line([(cx, cy), (cx + 70, cy + 40)], fill=(198, 40, 40, 255), width=22)
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(13, 60, 115, 255))
    return icon


def badge(icon, kind):
    img = icon.copy()
    d = ImageDraw.Draw(img)
    cx, cy, r = 770, 770, 230
    color = (46, 125, 50, 255) if kind == "setup" else (198, 40, 40, 255)
    d.ellipse([cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18], fill=(255, 255, 255, 255))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    w = 60
    if kind == "setup":                    # arrow down into a tray
        d.rectangle([cx - 38, cy - 150, cx + 38, cy + 20], fill="white")
        d.polygon([(cx - 120, cy + 0), (cx + 120, cy + 0), (cx, cy + 120)], fill="white")
        d.rectangle([cx - 140, cy + 140, cx + 140, cy + 165], fill="white")
    else:                                  # X
        k = 110
        d.line([(cx - k, cy - k), (cx + k, cy + k)], fill="white", width=w)
        d.line([(cx + k, cy - k), (cx - k, cy + k)], fill="white", width=w)
    return img


def save_ico(img, path):
    sizes = [(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.resize((256, 256), Image.LANCZOS).save(path, format="ICO", sizes=sizes)


def wizard_image(icon, w, h, path):
    img = gradient((w, h), (13, 60, 115), (41, 182, 246), diagonal=False)
    s = int(w * 0.7)
    ic = icon.resize((s, s), Image.LANCZOS)
    img.paste(ic, ((w - s) // 2, int(h * 0.12)), ic)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", max(10, w // 10))
        small = ImageFont.truetype("DejaVuSans.ttf", max(8, w // 15))
    except OSError:
        font = small = ImageFont.load_default()
    y = int(h * 0.12) + s + h // 20
    for text, f in (("Stopped", font), ("Flow", font), ("KinetiX", font)):
        tw = d.textlength(text, font=f)
        d.text(((w - tw) / 2, y), text, fill="white", font=f)
        y += int(f.size * 1.25)
    y += h // 30
    for text in ("stopped-flow CD", "kinetics analysis"):
        tw = d.textlength(text, font=small)
        d.text(((w - tw) / 2, y), text, fill=(227, 242, 253), font=small)
        y += int(small.size * 1.3)
    img.save(path, format="BMP")


def main():
    icon = base_icon()
    os.makedirs(os.path.join(ROOT, "resources", "icons"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "installer_assets"), exist_ok=True)
    icon.resize((256, 256), Image.LANCZOS).save(os.path.join(ROOT, "resources", "icons", "app_icon.png"))
    save_ico(icon, os.path.join(ROOT, "resources", "icons", "app_icon.ico"))
    save_ico(badge(icon, "setup"), os.path.join(ROOT, "installer_assets", "setupicon.ico"))
    save_ico(badge(icon, "uninstall"), os.path.join(ROOT, "installer_assets", "uninstall_icon.ico"))
    badge(icon, "setup").resize((256, 256), Image.LANCZOS).save(os.path.join(ROOT, "tools", "_setupicon_preview.png"))
    badge(icon, "uninstall").resize((256, 256), Image.LANCZOS).save(
        os.path.join(ROOT, "tools", "_uninstall_preview.png"))
    # Inno Setup 6 wizard images (100 % and high-DPI sizes)
    for w, h, suffix in ((164, 314, ""), (246, 459, "_150")):
        wizard_image(icon, w, h, os.path.join(ROOT, "installer_assets", f"wizardimage{suffix}.bmp"))
    for n, suffix in ((55, ""), (83, "_150")):
        small = Image.new("RGB", (n, n), "white")
        ic = icon.resize((n, n), Image.LANCZOS)
        small.paste(ic, (0, 0), ic)
        small.save(os.path.join(ROOT, "installer_assets", f"wizardsmallimage{suffix}.bmp"), format="BMP")
    print("icons written")


if __name__ == "__main__":
    main()
