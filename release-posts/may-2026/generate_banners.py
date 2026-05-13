from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1200, 780

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


F_LOGO = font(FONT_BOLD, 43)
F_LOGO_SUB = font(FONT_BOLD, 25)
F_HEAD = font(FONT_BLACK, 82)
F_HEAD_SMALL = font(FONT_BLACK, 70)
F_SUB = font(FONT_BOLD, 36)
F_CHIP = font(FONT_BOLD, 24)
F_SMALL = font(FONT_BOLD, 21)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def rounded_rectangle(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def make_background(seed: int, accent: tuple[int, int, int]) -> Image.Image:
    random.seed(seed)
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    px = img.load()
    base_a = (236, 250, 241)
    base_b = (82, 188, 136)
    base_c = (250, 250, 238)
    for y in range(H):
        for x in range(W):
            tx = x / W
            ty = y / H
            wave = 0.5 + 0.5 * math.sin((tx * 3.2 + ty * 2.1) * math.pi)
            t = min(1, max(0, ty * 0.76 + tx * 0.18 + wave * 0.08))
            r = lerp(base_a[0], base_b[0], t)
            g = lerp(base_a[1], base_b[1], t)
            b = lerp(base_a[2], base_b[2], t)
            warm = max(0, 1 - (tx * 1.2 + ty * 1.4))
            r = lerp(r, base_c[0], warm * 0.45)
            g = lerp(g, base_c[1], warm * 0.45)
            b = lerp(b, base_c[2], warm * 0.45)
            px[x, y] = (r, g, b, 255)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(9):
        y = 250 + i * 58 + random.randint(-22, 22)
        points = []
        for x in range(-80, W + 120, 40):
            yy = y + math.sin(x / 115 + i * 0.8) * (28 + i * 4)
            points.append((x, yy))
        d.line(points, fill=(255, 255, 255, 34), width=18)
        d.line(points, fill=(*accent, 24), width=6)

    for _ in range(90):
        x = random.randint(20, W - 20)
        y = random.randint(70, H - 30)
        r = random.choice([2, 2, 3, 4])
        color = random.choice([
            (255, 255, 255, 120),
            (255, 225, 94, 130),
            (*accent, 115),
        ])
        d.ellipse((x - r, y - r, x + r, y + r), fill=color)

    for _ in range(16):
        x = random.randint(50, W - 90)
        y = random.randint(120, H - 80)
        size = random.randint(13, 26)
        color = random.choice([(255, 255, 255, 125), (255, 225, 94, 145), (*accent, 145)])
        d.line((x - size // 2, y, x + size // 2, y), fill=color, width=5)
        d.line((x, y - size // 2, x, y + size // 2), fill=color, width=5)

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((760, 20, 1390, 520), fill=(255, 234, 111, 58))
    gd.ellipse((-260, 460, 410, 1030), fill=(*accent, 80))
    glow = glow.filter(ImageFilter.GaussianBlur(45))

    return Image.alpha_composite(Image.alpha_composite(img, glow), overlay)


def draw_logo(draw: ImageDraw.ImageDraw):
    x, y = 438, 64
    rounded_rectangle(draw, (x, y, x + 82, y + 82), 24, fill=(14, 134, 127, 255))
    cap_y = y + 38
    draw.polygon(
        [
            (x + 20, cap_y),
            (x + 41, cap_y - 13),
            (x + 64, cap_y),
            (x + 41, cap_y + 13),
        ],
        outline=(255, 255, 255, 255),
        fill=None,
    )
    draw.line((x + 27, cap_y + 6, x + 27, cap_y + 24, x + 54, cap_y + 24, x + 54, cap_y + 6), fill=(255, 255, 255, 255), width=4)
    draw.text((x + 104, y + 3), "Онкошкола", font=F_LOGO, fill=(36, 50, 58, 255))
    draw.text((x + 104, y + 50), "TASK MANAGER", font=F_LOGO_SUB, fill=(105, 130, 145, 255))


def draw_paper_plane(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0):
    pts = [
        (x, y + 36 * scale),
        (x + 118 * scale, y),
        (x + 74 * scale, y + 92 * scale),
        (x + 51 * scale, y + 57 * scale),
    ]
    draw.polygon(pts, fill=(31, 169, 225, 255), outline=(22, 122, 188, 255))
    draw.polygon([(x + 51 * scale, y + 57 * scale), (x + 118 * scale, y), (x + 62 * scale, y + 47 * scale)], fill=(118, 214, 245, 255))


def draw_bulb(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0):
    r = int(38 * scale)
    draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 215, 72, 255), outline=(255, 248, 160, 255), width=5)
    draw.rounded_rectangle((x - 18 * scale, y + 30 * scale, x + 18 * scale, y + 58 * scale), radius=int(8 * scale), fill=(245, 154, 33, 255))
    for a in range(0, 360, 45):
        dx = math.cos(math.radians(a)) * 60 * scale
        dy = math.sin(math.radians(a)) * 60 * scale
        draw.line((x + dx * 0.72, y + dy * 0.72, x + dx, y + dy), fill=(255, 235, 107, 190), width=max(2, int(4 * scale)))


def draw_checklist(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0):
    w, h = int(160 * scale), int(210 * scale)
    rounded_rectangle(draw, (x, y, x + w, y + h), int(22 * scale), fill=(246, 255, 249, 240), outline=(66, 175, 124, 180), width=3)
    draw.rectangle((x + 36 * scale, y - 15 * scale, x + 125 * scale, y + 20 * scale), fill=(83, 143, 142, 255))
    for i in range(4):
        yy = y + 50 * scale + i * 36 * scale
        draw.rounded_rectangle((x + 25 * scale, yy, x + 47 * scale, yy + 22 * scale), radius=5, outline=(40, 166, 104, 255), width=3)
        draw.line((x + 29 * scale, yy + 11 * scale, x + 36 * scale, yy + 18 * scale, x + 47 * scale, yy + 3 * scale), fill=(40, 166, 104, 255), width=4)
        draw.line((x + 64 * scale, yy + 11 * scale, x + 132 * scale, yy + 11 * scale), fill=(91, 127, 127, 185), width=5)


def draw_calendar(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0):
    w, h = int(200 * scale), int(165 * scale)
    rounded_rectangle(draw, (x, y, x + w, y + h), int(24 * scale), fill=(244, 254, 246, 235), outline=(69, 174, 125, 170), width=3)
    draw.rounded_rectangle((x, y, x + w, y + 45 * scale), int(20 * scale), fill=(39, 151, 121, 255))
    for cx in [x + 48 * scale, x + 152 * scale]:
        draw.line((cx, y - 12 * scale, cx, y + 20 * scale), fill=(45, 80, 88, 255), width=8)
    for row in range(2):
        for col in range(4):
            bx = x + 28 * scale + col * 42 * scale
            by = y + 70 * scale + row * 38 * scale
            fill = (52, 183, 116, 255) if (row, col) in [(0, 1), (1, 2)] else (211, 236, 221, 255)
            rounded_rectangle(draw, (bx, by, bx + 24 * scale, by + 22 * scale), 5, fill=fill)


def draw_cards(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0):
    for i, color in enumerate([(255, 255, 255, 245), (245, 255, 248, 245), (255, 255, 255, 245)]):
        yy = y + i * 62 * scale
        rounded_rectangle(draw, (x + i * 15 * scale, yy, x + 220 * scale + i * 15 * scale, yy + 46 * scale), int(18 * scale), fill=color, outline=(76, 172, 134, 140), width=2)
        draw.ellipse((x + 16 * scale + i * 15 * scale, yy + 10 * scale, x + 42 * scale + i * 15 * scale, yy + 36 * scale), fill=(255, 180, 65, 255))
        draw.line((x + 56 * scale + i * 15 * scale, yy + 18 * scale, x + 154 * scale + i * 15 * scale, yy + 18 * scale), fill=(97, 126, 128, 170), width=5)
        draw.line((x + 56 * scale + i * 15 * scale, yy + 31 * scale, x + 130 * scale + i * 15 * scale, yy + 31 * scale), fill=(151, 177, 173, 145), width=4)
        draw.ellipse((x + 178 * scale + i * 15 * scale, yy + 11 * scale, x + 203 * scale + i * 15 * scale, yy + 36 * scale), fill=(45, 181, 106, 255))
        draw.line((x + 184 * scale + i * 15 * scale, yy + 25 * scale, x + 192 * scale + i * 15 * scale, yy + 32 * scale, x + 202 * scale + i * 15 * scale, yy + 17 * scale), fill=(255, 255, 255, 255), width=3)


def draw_chart(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0):
    rounded_rectangle(draw, (x, y, x + 240 * scale, y + 180 * scale), int(26 * scale), fill=(247, 255, 249, 238), outline=(61, 165, 122, 170), width=3)
    bars = [52, 86, 118, 74]
    colors = [(245, 96, 96, 255), (42, 170, 113, 255), (24, 141, 130, 255), (255, 199, 77, 255)]
    for i, bh in enumerate(bars):
        bx = x + 34 * scale + i * 46 * scale
        by = y + 140 * scale - bh * scale
        rounded_rectangle(draw, (bx, by, bx + 26 * scale, y + 140 * scale), int(8 * scale), fill=colors[i])
    draw.line((x + 30 * scale, y + 148 * scale, x + 208 * scale, y + 148 * scale), fill=(91, 127, 127, 170), width=4)
    draw.line((x + 33 * scale, y + 54 * scale, x + 77 * scale, y + 78 * scale, x + 121 * scale, y + 45 * scale, x + 170 * scale, y + 70 * scale, x + 210 * scale, y + 40 * scale), fill=(26, 137, 126, 255), width=6)


def draw_waveform(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0):
    rounded_rectangle(draw, (x, y, x + 260 * scale, y + 160 * scale), int(30 * scale), fill=(247, 255, 249, 238), outline=(61, 165, 122, 170), width=3)
    cx = x + 38 * scale
    for i, h in enumerate([28, 55, 88, 48, 98, 64, 34, 76, 44, 106, 58]):
        xx = cx + i * 18 * scale
        draw.line((xx, y + 82 * scale - h * scale / 2, xx, y + 82 * scale + h * scale / 2), fill=(25, 139, 129, 255), width=max(3, int(7 * scale)))
    draw.ellipse((x + 202 * scale, y + 26 * scale, x + 240 * scale, y + 64 * scale), fill=(255, 213, 67, 255))
    draw.text((x + 210 * scale, y + 69 * scale), "AI", font=font(FONT_BLACK, int(28 * scale)), fill=(25, 96, 96, 255))


def draw_flow(draw: ImageDraw.ImageDraw, points, color=(255, 255, 255, 165)):
    for idx in range(len(points) - 1):
        draw.line((points[idx], points[idx + 1]), fill=color, width=5)
    for x, y in points[1:]:
        draw.polygon([(x, y), (x - 18, y - 8), (x - 13, y + 10)], fill=color)


def centered_text(draw: ImageDraw.ImageDraw, text: str, y: int, fnt, fill, stroke_fill=None, stroke_width=0):
    box = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke_width)
    x = (W - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=fnt, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def draw_banner(spec: dict):
    img = make_background(spec["seed"], spec["accent"])
    d = ImageDraw.Draw(img)

    draw_logo(d)

    capsule = (218, 248, 982, 430)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    rounded_rectangle(sd, (capsule[0] + 8, capsule[1] + 14, capsule[2] + 8, capsule[3] + 14), 58, fill=(5, 76, 63, 95))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(shadow)
    d = ImageDraw.Draw(img)

    rounded_rectangle(d, capsule, 58, fill=(12, 116, 86, 230), outline=(218, 255, 226, 155), width=3)
    d.line((capsule[0] + 55, capsule[3] - 35, capsule[2] - 55, capsule[3] - 35), fill=(255, 233, 92, 160), width=5)

    headline_font = F_HEAD if len(spec["headline"]) <= 18 else F_HEAD_SMALL
    centered_text(d, spec["headline"], 282, headline_font, (255, 255, 255, 255), stroke_fill=(5, 82, 66, 210), stroke_width=3)
    centered_text(d, spec["subhead"], 446, F_SUB, (18, 91, 83, 255))

    chip_w = 180 if len(spec["chip"]) <= 8 else 230
    rounded_rectangle(d, (W - chip_w - 78, 64, W - 78, 112), 24, fill=(255, 255, 255, 195), outline=(255, 255, 255, 220), width=2)
    d.text((W - chip_w - 52, 78), spec["chip"], font=F_CHIP, fill=(23, 126, 103, 255))

    if spec["kind"] == "overview":
        draw_checklist(d, 90, 448, 0.92)
        draw_calendar(d, 468, 548, 0.9)
        draw_cards(d, 845, 470, 0.82)
        draw_bulb(d, 1010, 215, 0.8)
        draw_paper_plane(d, 968, 578, 0.9)
        draw_flow(d, [(232, 582), (430, 532), (607, 586), (810, 545), (930, 612)], (*spec["accent"], 175))
    elif spec["kind"] == "ideas":
        draw_bulb(d, 164, 530, 1.15)
        draw_cards(d, 830, 458, 0.92)
        draw_checklist(d, 468, 520, 0.78)
        draw_flow(d, [(244, 532), (420, 548), (612, 560), (810, 526)], (*spec["accent"], 175))
        for label, x, y in [("Идея", 108, 638), ("Проект", 468, 700), ("Задачи", 837, 646)]:
            rounded_rectangle(d, (x, y, x + 142, y + 44), 22, fill=(255, 255, 255, 180))
            d.text((x + 24, y + 10), label, font=F_SMALL, fill=(18, 91, 83, 255))
    elif spec["kind"] == "tasks":
        draw_checklist(d, 106, 450, 1.06)
        draw_cards(d, 814, 460, 0.95)
        for i, (label, color) in enumerate([("Метки", (36, 168, 122)), ("Фильтры", (35, 145, 189)), ("Срочно", (230, 84, 76))]):
            x = 420 + i * 145
            rounded_rectangle(d, (x, 594, x + 126, 642), 24, fill=(*color, 235))
            d.text((x + 20, 607), label, font=F_SMALL, fill=(255, 255, 255, 255))
    elif spec["kind"] == "dashboard":
        draw_chart(d, 104, 468, 1.05)
        draw_calendar(d, 846, 492, 0.95)
        for i, label in enumerate(["Просрочено", "Активные", "7 дней"]):
            x = 438 + i * 165
            rounded_rectangle(d, (x, 590, x + 142, 638), 22, fill=(255, 255, 255, 185))
            d.text((x + 18, 603), label, font=F_SMALL, fill=(18, 91, 83, 255))
    elif spec["kind"] == "meetings":
        draw_waveform(d, 104, 490, 1.05)
        draw_calendar(d, 842, 492, 0.95)
        draw_cards(d, 478, 544, 0.72)
        draw_flow(d, [(345, 560), (470, 594), (690, 592), (838, 566)], (*spec["accent"], 175))

    rounded_rectangle(d, (0, 0, W - 1, H - 1), 42, fill=None, outline=(255, 255, 255, 110), width=3)
    img = img.convert("RGB")
    out = OUT_DIR / spec["filename"]
    img.save(out, quality=95)
    return out


SPECS = [
    {
        "filename": "01-may-release-overview.png",
        "headline": "МАЙСКОЕ ОБНОВЛЕНИЕ",
        "subhead": "Портал стал заметно больше",
        "chip": "МАЙ 2026",
        "kind": "overview",
        "seed": 11,
        "accent": (20, 152, 111),
    },
    {
        "filename": "02-ideas-projects.png",
        "headline": "ИДЕИ И ПРОЕКТЫ",
        "subhead": "От предложения до результата",
        "chip": "НОВЫЙ БЛОК",
        "kind": "ideas",
        "seed": 21,
        "accent": (23, 151, 122),
    },
    {
        "filename": "03-tasks-upgrade.png",
        "headline": "ЗАДАЧИ СТАЛИ УДОБНЕЕ",
        "subhead": "Метки, фильтры, срочность",
        "chip": "ЗАДАЧИ",
        "kind": "tasks",
        "seed": 31,
        "accent": (35, 154, 115),
    },
    {
        "filename": "04-dashboard-focus.png",
        "headline": "ДАШБОРД БЕЗ ДУБЛЕЙ",
        "subhead": "Фокус на важном каждый день",
        "chip": "ДАШБОРД",
        "kind": "dashboard",
        "seed": 41,
        "accent": (25, 142, 130),
    },
    {
        "filename": "05-meetings-ai.png",
        "headline": "ВСТРЕЧИ И AI-ИТОГИ",
        "subhead": "Доска, транскрибация, задачи",
        "chip": "ВСТРЕЧИ",
        "kind": "meetings",
        "seed": 51,
        "accent": (22, 146, 129),
    },
]


if __name__ == "__main__":
    for spec in SPECS:
        print(draw_banner(spec))
