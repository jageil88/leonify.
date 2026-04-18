"""Erzeugt icon.png und presplash.png aus dem Logo-design.

Wird im GitHub Actions build automatisch ausgeführt bevor buildozer läuft.
"""

import os

from PIL import Image, ImageDraw


# Farben (muss mit theme.py übereinstimmen)
BG = (10, 10, 18, 255)
PRIMARY = (168, 85, 247, 255)   # #A855F7
SECONDARY = (236, 72, 153, 255)  # #EC4899


def draw_l_logo(img_size: int, padding: int = 0) -> Image.Image:
    """Zeichnet das Leonify-logo (dunkler rounded square mit L + EQ-bars)."""
    scale = img_size / 512.0
    s = lambda x: int(x * scale)

    img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # rounded square hintergrund
    draw.rounded_rectangle(
        [(padding, padding), (img_size - padding, img_size - padding)],
        radius=s(112),
        fill=BG,
    )

    # vertical stroke des L
    l_x1 = s(120)
    l_x2 = s(160)
    l_y1 = s(130)
    l_y2 = s(400)
    draw.rounded_rectangle([(l_x1, l_y1), (l_x2, l_y2)], radius=s(10), fill=PRIMARY)

    # equalizer bars (formen die basis des L)
    bars = [
        (180, 340, 208, 400),
        (220, 290, 248, 400),
        (260, 320, 288, 400),
        (300, 260, 328, 400),
        (340, 350, 368, 400),
    ]
    for (x1, y1, x2, y2) in bars:
        draw.rounded_rectangle(
            [(s(x1), s(y1)), (s(x2), s(y2))],
            radius=s(10),
            fill=SECONDARY,
        )

    return img


def draw_presplash(width: int, height: int) -> Image.Image:
    """Presplash screen - logo zentriert auf BG."""
    img = Image.new("RGBA", (width, height), BG)

    # logo-icon in der mitte
    logo_size = min(width, height) // 3
    logo = draw_l_logo(logo_size)

    # center position
    x = (width - logo_size) // 2
    y = (height - logo_size) // 2

    img.paste(logo, (x, y), logo)
    return img


def main():
    os.makedirs("assets", exist_ok=True)

    # app icon (512x512 für android)
    icon = draw_l_logo(512)
    icon.save("assets/icon.png")
    print("→ assets/icon.png (512x512)")

    # auch im root speichern weil buildozer.spec dort sucht
    icon.save("icon.png")
    print("→ icon.png")

    # presplash (1920x1920 quadratisch, wird skaliert)
    presplash = draw_presplash(1920, 1920)
    presplash.save("presplash.png")
    print("→ presplash.png (1920x1920)")


if __name__ == "__main__":
    main()
