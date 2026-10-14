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
    badge = Image.new("RGBA", size, (255, 255, 255, 255))
    badge_draw = ImageDraw.Draw(badge)
    badge_draw.rounded_rectangle((0, 0, badge_width - 1, badge_height - 1), radius=34, outline="#D7E7E7", width=4)
    badge_draw.rounded_rectangle((10, 10, badge_width - 11, badge_height - 11), radius=27, outline=PALE_GOLD, width=2)
    logo = ImageOps.contain(trimmed_logo(logo_path), (badge_width - 48, badge_height - 48), Image.Resampling.LANCZOS).convert("RGBA")
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


def vertical_gradient(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    background = Image.new("RGB", (WIDTH, HEIGHT), top)
    gradient = ImageDraw.Draw(background)
    for y in range(HEIGHT):
        fraction = y / (HEIGHT - 1)
        colour = tuple(round(top[index] + (bottom[index] - top[index]) * fraction) for index in range(3))
        gradient.line((0, y, WIDTH, y), fill=colour)
    return background.convert("RGBA")


def pill(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], number: str, label: str) -> None:
    left, top, right, bottom = box
    draw.rounded_rectangle(box, radius=(bottom - top) // 2, fill="#EDF6F5", outline="#D3E9E8", width=2)
    circle_size = bottom - top - 18
    circle_left = left + 10
    draw.ellipse((circle_left, top + 9, circle_left + circle_size, bottom - 9), fill=TEAL)
    number_font = font(BOLD_FONT, 24)
    label_font = font(BOLD_FONT, 24)
    centered_text(draw, number, top + 19, number_font, WHITE, center=circle_left + circle_size // 2)
    draw.text((circle_left + circle_size + 18, top + 20), label, font=label_font, fill=DEEP_TEAL)


def build_poster() -> Image.Image:
    canvas = vertical_gradient((249, 251, 251), (239, 247, 246))
    draw = ImageDraw.Draw(canvas)

    # A single restrained curve gives the poster depth while retaining a clinical feel.
    draw.arc((390, 935, 2730, 3310), 140, 305, fill="#D2E7E6", width=16)
    draw.arc((530, 1040, 2630, 3200), 145, 290, fill="#F0DBB5", width=5)

    # Branded header.
    draw.rounded_rectangle((100, 105, WIDTH - 100, 935), radius=80, fill=TEAL)
    draw.rounded_rectangle((118, 123, WIDTH - 118, 917), radius=68, outline="#6AA4AC", width=2)
    add_logo_badge(canvas, ASSETS / "father-muller-portrait.jpg", 160, 155, (300, 255))
    add_logo_badge(canvas, ASSETS / "father-muller-crest.jpg", WIDTH - 460, 155, (300, 255))

    header_regular = font(REGULAR_FONT, 32)
    header_bold = font(BOLD_FONT, 44)
    tiny_caps = font(BOLD_FONT, 27)
    title_font = font(ARIAL_BOLD_FONT, 122)
    title_gold_font = font(ARIAL_BOLD_FONT, 144)
    subtitle_font = font(REGULAR_FONT, 35)

    centered_text(draw, "FATHER MULLER MEDICAL COLLEGE", 158, header_bold, WHITE)
    centered_text(draw, "Department of Dermatology  •  Department of Rheumatology", 219, header_regular, "#D4ECED")
    draw.line((690, 297, 1790, 297), fill="#82B8C0", width=2)
    centered_text(draw, "PRESENT", 328, tiny_caps, "#D4ECED")
    centered_text(draw, "PSORIASIS WEEK", 375, header_bold, GOLD)
    centered_text(draw, "LOOK BEYOND", 460, title_font, WHITE)
    centered_text(draw, "YOUR SKIN", 600, title_gold_font, "#F7DDA8")
    centered_text(draw, "A short Psoriatic Arthritis screening for people with Psoriasis", 787, subtitle_font, WHITE)
    centered_text(draw, "Your skin is only part of the story.", 846, font(REGULAR_FONT, 29), "#D4ECED")

    # Main message card.
    draw.rounded_rectangle((230, 1075, WIDTH - 230, 1715), radius=54, fill=WHITE, outline="#D7E9E8", width=3)
    section_label = font(BOLD_FONT, 29)
    message_font = font(BOLD_FONT, 43)
    body_font = font(REGULAR_FONT, 31)
    ghost_five = font(ARIAL_BOLD_FONT, 220)
    draw.text((320, 1172), "5", font=ghost_five, fill="#EAF4F3")
    centered_text(draw, "A QUICK JOINT HEALTH CHECK", 1162, section_label, TEAL)
    centered_wrapped_text(
        draw,
        "Psoriatic Arthritis can affect the joints, heels, fingers, toes and back."
        " A short screen can help you start the conversation with your dermatologist.",
        1232,
        message_font,
        INK,
        1580,
        15,
    )
    draw.line((665, 1458, 1815, 1458), fill="#E5EEEE", width=2)
    pill(draw, (455, 1515, 960, 1585), "1", "Scan")
    pill(draw, (988, 1515, 1507, 1585), "2", "Answer 5 questions")
    pill(draw, (1535, 1515, 2030, 1585), "3", "Share")
    centered_text(draw, "Screening support only  •  Not a diagnosis", 1632, body_font, "#4D6067")

    # The scan area is deliberately uncluttered so it remains the visual destination.
    draw.rounded_rectangle((510, 1875, WIDTH - 510, 3215), radius=78, fill="#FBFEFE", outline="#D6E9E8", width=3)
    draw.ellipse((724, 2065, 1756, 3097), outline="#D8A958", width=5)
    draw.ellipse((744, 2085, 1736, 3077), outline="#DDEDEC", width=3)
    scan_heading = font(BOLD_FONT, 45)
    scan_body = font(REGULAR_FONT, 30)
    scan_small = font(REGULAR_FONT, 26)
    centered_text(draw, "SCAN TO COMPLETE YOUR SCREENING", 1955, scan_heading, TEAL)
    centered_text(draw, "Open the questionnaire with your phone camera", 2025, scan_body, "#536771")

    qr_image = create_qr_code(640)
    qr_panel = Image.new("RGBA", (730, 730), (255, 255, 255, 255))
    panel_draw = ImageDraw.Draw(qr_panel)
    panel_draw.rounded_rectangle((2, 2, 727, 727), radius=35, outline="#E6EBEC", width=4)
    qr_panel.alpha_composite(qr_image, ((730 - qr_image.width) // 2, (730 - qr_image.height) // 2))
    canvas.alpha_composite(qr_panel, ((WIDTH - qr_panel.width) // 2, 2180))

    centered_text(draw, "Please have your UHID ready. Do not enter your name or phone number.", 2995, scan_small, "#5E6F78")

    # Footer with the full public address for people who cannot scan.
    draw.rounded_rectangle((100, 3328, WIDTH - 100, 3422), radius=36, fill=DEEP_TEAL)
    footer_font = font(REGULAR_FONT, 26)
    centered_text(draw, "nbhushan15.github.io/psa-clinic-mvp", 3362, footer_font, WHITE)
    return canvas.convert("RGB")


if __name__ == "__main__":
    output = build_poster()
    output.save(OUTPUT, format="PNG", dpi=(300, 300), optimize=True)
    print(f"Created {OUTPUT}")
