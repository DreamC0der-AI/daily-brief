"""Generate 1200x630 social preview cards (one per day per language) and QR codes."""
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode, qrcode.image.svg

W, H = 1200, 630
BG, FG, MUTED, ACCENT = (27, 26, 23), (246, 244, 238), (161, 156, 144), (224, 112, 74)

SERIF = ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"]
CJK = ["/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/PingFang.ttc",
       "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
       "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"]
SANS = ["/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]


def font(cands, size):
    for p in cands:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


def wrap(draw, text, fnt, max_w, max_lines):
    """Greedy wrap: Latin words stay whole, CJK breaks per character, spaces preserved."""
    import re
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9.'’\-]*|\s+|.", text)
    lines, cur = [], ""
    for i, tok in enumerate(tokens):
        trial = cur + tok
        if draw.textlength(trial.rstrip(), font=fnt) <= max_w:
            cur = trial
        else:
            lines.append(cur.rstrip()); cur = tok.lstrip()
            if len(lines) == max_lines:
                lines[-1] = lines[-1].rstrip(" ,;:，、：") + "…"
                return lines
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def card(date_label, headlines, lang, out_path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    brand = font(SERIF, 44)
    d.text((72, 56), "Daily", font=brand, fill=FG)
    d.text((72 + d.textlength("Daily", font=brand), 56), "Brief", font=brand, fill=ACCENT)
    date_f = font(CJK if lang == "zh" else SANS, 26)
    d.text((W - 72 - d.textlength(date_label, font=date_f), 66), date_label, font=date_f, fill=MUTED)
    d.line((72, 122, W - 72, 122), fill=(60, 58, 52), width=2)
    hf = font(CJK if lang == "zh" else SERIF, 40 if lang == "zh" else 38)
    y = 150
    for i, h in enumerate(headlines[:3], 1):
        num_f = font(SERIF, 24)
        d.text((72, y + 8), f"{i:02d}", font=num_f, fill=ACCENT)
        lines = wrap(d, h, hf, W - 72 - 130, 2)
        for ln in lines:
            d.text((130, y), ln, font=hf, fill=FG)
            y += 50 if lang == "zh" else 48
        y += 22
        if y > H - 120:
            break
    foot = font(CJK if lang == "zh" else SANS, 22)
    d.text((72, H - 64), "dreamc0der-ai.github.io/daily-brief" + ("  ·  中文版" if lang == "zh" else ""), font=foot, fill=MUTED)
    img.save(out_path, "PNG", optimize=True)


def square(date_short, headline, lang, out_path):
    """400x400 thumbnail WeChat uses for chat/Moments cards (first image >=300px on the page)."""
    S = 400
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)
    brand = font(SERIF, 44)
    d.text((32, 34), "Daily", font=brand, fill=FG)
    d.text((32 + d.textlength("Daily", font=brand), 34), "Brief", font=brand, fill=ACCENT)
    df = font(CJK if lang == "zh" else SANS, 22)
    d.text((32, 92), date_short, font=df, fill=MUTED)
    d.line((32, 128, S - 32, 128), fill=(60, 58, 52), width=2)
    hf = font(CJK if lang == "zh" else SERIF, 30 if lang == "zh" else 28)
    y = 150
    for ln in wrap(d, headline, hf, S - 64, 5):
        d.text((32, y), ln, font=hf, fill=FG)
        y += 40 if lang == "zh" else 38
    d.text((32, S - 48), "中文版" if lang == "zh" else "dreamc0der-ai.github.io", font=font(CJK if lang == "zh" else SANS, 18), fill=MUTED)
    img.save(out_path, "PNG", optimize=True)


def qr_svg(url):
    """Compact inline SVG QR code as a string."""
    q = qrcode.QRCode(border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(url)
    img = q.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    buf = io.BytesIO(); img.save(buf)
    svg = buf.getvalue().decode()
    return svg[svg.index("<svg"):]
