"""Create the print-ready Look Beyond Your Skin campaign poster.

The poster is A4 portrait at 300 dpi and its QR code points to the public
screening page. Run from any directory with:

    python3 -m pip install "qrcode[pil]"
    python3 scripts/create_campaign_poster.py
"""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
import qrcode


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ASSETS / "look-beyond-your-skin-poster.png"
QR_OUTPUT = ASSETS / "psa-screening-qr.png"
PUBLIC_SCREENING_URL = "https://nbhushan15.github.io/psa-clinic-mvp/"

WIDTH, HEIGHT = 2480, 3508  # A4 at 300 dpi
TEAL = "#116776"
DEEP_TEAL = "#0B4F5C"
INK = "#13212C"
GOLD = "#D69D42"
PALE_GOLD = "#F5E7CB"
MIST = "#F4F8F8"
WHITE = "#FFFFFF"

REGULAR_FONT = "/System/Library/Fonts/Supplemental/Verdana.ttf"
BOLD_FONT = "/System/Library/Fonts/Supplemental/Verdana Bold.ttf"
ARIAL_BOLD_FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def text_width(draw: ImageDraw.ImageDraw, value: str, text_font: ImageFont.FreeTypeFont) -> int:
    left, _, right, _ = draw.textbbox((0, 0), value, font=text_font)
    return right - left


def centered_text(
    draw: ImageDraw.ImageDraw,
    value: str,
    y: int,
    text_font: ImageFont.FreeTypeFont,
    fill: str,
    *,
    center: int = WIDTH // 2,
) -> None:
    draw.text((center - text_width(draw, value, text_font) / 2, y), value, font=text_font, fill=fill)


def wrap_lines(
    draw: ImageDraw.ImageDraw,
    value: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    words = value.split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if line and text_width(draw, candidate, text_font) > max_width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def centered_wrapped_text(
    draw: ImageDraw.ImageDraw,
    value: str,
    y: int,
    text_font: ImageFont.FreeTypeFont,
    fill: str,
    max_width: int,
    line_gap: int,
) -> int:
    line_height = draw.textbbox((0, 0), "Ag", font=text_font)[3]
    for line in wrap_lines(draw, value, text_font, max_width):
        centered_text(draw, line, y, text_font, fill)
        y += line_height + line_gap
    return y


def trimmed_logo(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    white = Image.new("RGB", image.size, "white")
    difference = ImageChops.difference(image, white).convert("L")
    mask = difference.point(lambda pixel: 255 if pixel > 18 else 0)
    bounds = mask.getbbox()
    return image.crop(bounds) if bounds else image


def add_logo_badge(canvas: Image.Image, logo_path: Path, x: int, y: int, size: tuple[int, int]) -> None:
    badge_width, badge_height = size
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (x + 10, y + 14, x + badge_width + 10, y + badge_height + 14),
        radius=38,
        fill=(0, 0, 0, 36),
    )
    canvas.alpha_composite(shadow)

    badge = Image.new("RGBA", size, (255, 255, 255, 255))
    badge_draw = ImageDraw.Draw(badge)
    badge_draw.rounded_rectangle((0, 0, badge_width - 1, badge_height - 1), radius=38, outline=PALE_GOLD, width=5)
    logo = ImageOps.contain(trimmed_logo(logo_path), (badge_width - 56, badge_height - 56), Image.Resampling.LANCZOS).convert("RGBA")
    badge.alpha_composite(logo, ((badge_width - logo.width) // 2, (badge_height - logo.height) // 2))
    canvas.alpha_composite(badge, (x, y))


def create_qr_code(size: int) -> Image.Image:
    code = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=16,
        border=4,
    )
    code.add_data(PUBLIC_SCREENING_URL)
    code.make(fit=True)
    source = code.make_image(fill_color=INK, back_color=WHITE).convert("RGBA")
    source.save(QR_OUTPUT, format="PNG")
    return source.resize((size, size), Image.Resampling.NEAREST)


def build_poster() -> Image.Image:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), MIST)
    draw = ImageDraw.Draw(canvas)

    # Soft background geometry keeps the page warm without competing with the QR code.
    draw.ellipse((-430, 950, 520, 1900), fill="#E3F0EF")
    draw.ellipse((1970, 1280, 2940, 2250), fill="#F8EEDC")
    draw.arc((165, 1190, 2315, 3350), 200, 340, fill="#D9E9E8", width=18)

    # Branded header.
    draw.rounded_rectangle((100, 105, WIDTH - 100, 1040), radius=84, fill=TEAL)
    draw.rounded_rectangle((118, 123, WIDTH - 118, 1022), radius=72, outline="#4D94A0", width=3)
    add_logo_badge(canvas, ASSETS / "father-muller-portrait.jpg", 160, 170, (360, 310))
    add_logo_badge(canvas, ASSETS / "father-muller-crest.jpg", WIDTH - 520, 170, (360, 310))

    header_regular = font(REGULAR_FONT, 35)
    header_bold = font(BOLD_FONT, 48)
    tiny_caps = font(BOLD_FONT, 27)
    title_font = font(ARIAL_BOLD_FONT, 126)
    title_gold_font = font(ARIAL_BOLD_FONT, 148)
    subtitle_font = font(REGULAR_FONT, 39)

    centered_text(draw, "FATHER MULLER MEDICAL COLLEGE", 170, header_bold, WHITE)
    centered_text(draw, "Department of Dermatology  •  Department of Rheumatology", 238, header_regular, "#D4ECED")
    draw.line((710, 330, 1770, 330), fill="#82B8C0", width=3)
    centered_text(draw, "PRESENT", 370, tiny_caps, "#D4ECED")
    centered_text(draw, "PSORIASIS WEEK", 425, header_bold, GOLD)
    centered_text(draw, "LOOK BEYOND", 522, title_font, WHITE)
    centered_text(draw, "YOUR SKIN", 671, title_gold_font, "#F7DDA8")
    centered_text(draw, "A short Psoriatic Arthritis screening for people with Psoriasis", 862, subtitle_font, WHITE)

    # Main message card.
    draw.rounded_rectangle((230, 1170, WIDTH - 230, 2045), radius=54, fill=WHITE, outline="#D3E7E8", width=4)
    section_label = font(BOLD_FONT, 32)
    message_font = font(BOLD_FONT, 50)
    body_font = font(REGULAR_FONT, 36)
    centered_text(draw, "A QUICK JOINT HEALTH CHECK", 1260, section_label, TEAL)
    centered_wrapped_text(
        draw,
        "Psoriatic Arthritis can affect the joints, heels, fingers, toes and back."
        " A short screen can help you start the conversation with your dermatologist.",
        1340,
        message_font,
        INK,
        1670,
        18,
    )
    draw.line((575, 1570, 1905, 1570), fill="#E7F0F0", width=3)
    centered_wrapped_text(
        draw,
        "Scan the code, answer five questions, and share the result during your dermatology consultation.",
        1650,
        body_font,
        "#3A4C56",
        1540,
        15,
    )
    draw.rounded_rectangle((720, 1870, 1760, 1945), radius=32, fill="#E9F4F3")
    centered_text(draw, "SCREENING SUPPORT ONLY  •  NOT A DIAGNOSIS", 1888, section_label, DEEP_TEAL)

    # Scan card.
    draw.rounded_rectangle((420, 2160, WIDTH - 420, 3230), radius=60, fill=WHITE, outline="#D3E7E8", width=4)
    scan_heading = font(BOLD_FONT, 48)
    scan_body = font(REGULAR_FONT, 32)
    scan_small = font(REGULAR_FONT, 27)
    centered_text(draw, "SCAN TO COMPLETE YOUR SCREENING", 2245, scan_heading, TEAL)
    centered_text(draw, "Open the questionnaire with your phone camera", 2325, scan_body, "#3A4C56")

    qr_image = create_qr_code(620)
    qr_panel = Image.new("RGBA", (710, 710), (255, 255, 255, 255))
    panel_draw = ImageDraw.Draw(qr_panel)
    panel_draw.rounded_rectangle((2, 2, 707, 707), radius=35, outline="#E5E9EB", width=4)
    qr_panel.alpha_composite(qr_image, ((710 - qr_image.width) // 2, (710 - qr_image.height) // 2))
    canvas.alpha_composite(qr_panel, ((WIDTH - qr_panel.width) // 2, 2420))

    centered_text(draw, "Please have your UHID ready. Do not enter your name or phone number.", 3155, scan_small, "#5E6F78")

    # Footer with the full public address for people who cannot scan.
    draw.rounded_rectangle((100, 3328, WIDTH - 100, 3422), radius=36, fill=DEEP_TEAL)
    footer_font = font(REGULAR_FONT, 26)
    centered_text(draw, "nbhushan15.github.io/psa-clinic-mvp", 3362, footer_font, WHITE)
    return canvas.convert("RGB")


if __name__ == "__main__":
    output = build_poster()
    output.save(OUTPUT, format="PNG", dpi=(300, 300), optimize=True)
    print(f"Created {OUTPUT}")
