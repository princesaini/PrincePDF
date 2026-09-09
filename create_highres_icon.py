"""
Generates ultra high-resolution Windows 11 Fluent-style app icons for PrincePDF.
Renders at 2048x2048 supersampled down to 1024x1024 with Lanczos filtering,
and bundles all standard Windows 11 multi-resolution layers into app_icon.ico.
"""

import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def create_highres_icon():
    os.makedirs("resources", exist_ok=True)

    # Render at 2048x2048 for 2x supersampling to guarantee crisp vector-like edges
    S = 2048
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Subtle drop shadow behind the main card
    shadow_pad = int(S * 0.08)
    shadow_rect = [
        (shadow_pad, shadow_pad + int(S * 0.04)),
        (S - shadow_pad, S - shadow_pad + int(S * 0.04))
    ]
    shadow_img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    shadow_draw.rounded_rectangle(shadow_rect, radius=int(S * 0.22), fill=(0, 0, 0, 95))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=int(S * 0.035)))
    img = Image.alpha_composite(img, shadow_img)
    draw = ImageDraw.Draw(img)

    # 2. Main squircle background with vertical gradient (Vibrant Fluent Red / Crimson)
    card_pad = int(S * 0.08)
    card_w = S - 2 * card_pad
    card_h = S - 2 * card_pad
    card_r = int(S * 0.22)

    # Gradient mask
    card_mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle(
        [(card_pad, card_pad), (S - card_pad, S - card_pad)],
        radius=card_r, fill=255
    )

    card_gradient = Image.new("RGBA", (S, S))
    for y in range(card_pad, S - card_pad):
        prog = (y - card_pad) / max(1, card_h)
        # Gradient from deep modern ruby red (225, 29, 72) to vivid scarlet (239, 68, 68)
        r = int(225 + prog * (200 - 225))
        g = int(29 + prog * (15 - 29))
        b = int(72 + prog * (45 - 72))
        for x in range(card_pad, S - card_pad):
            card_gradient.putpixel((x, y), (r, g, b, 255))

    img.paste(card_gradient, (0, 0), card_mask)
    draw = ImageDraw.Draw(img)

    # 3. Inner White Folded Document Sheet
    doc_pad_x = int(S * 0.24)
    doc_top = int(S * 0.20)
    doc_right = int(S * 0.76)
    doc_bottom = int(S * 0.80)
    doc_r = int(S * 0.06)

    # Subtle document shadow
    doc_shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(doc_shadow).rounded_rectangle(
        [(doc_pad_x, doc_top + int(S * 0.02)), (doc_right, doc_bottom + int(S * 0.02))],
        radius=doc_r, fill=(0, 0, 0, 50)
    )
    doc_shadow = doc_shadow.filter(ImageFilter.GaussianBlur(radius=int(S * 0.02)))
    img = Image.alpha_composite(img, doc_shadow)
    draw = ImageDraw.Draw(img)

    # Document body (Crisp pure white with smooth corners)
    draw.rounded_rectangle(
        [(doc_pad_x, doc_top), (doc_right, doc_bottom)],
        radius=doc_r,
        fill=(255, 255, 255, 255)
    )

    # 4. Folded Top-Right Corner of the Document
    fold_size = int(S * 0.14)
    # White document with corner folded:
    # Corner triangle background
    corner_poly = [
        (doc_right - fold_size, doc_top),
        (doc_right, doc_top + fold_size),
        (doc_right, doc_top)
    ]
    draw.polygon(corner_poly, fill=(225, 29, 72, 255)) # match card background

    # Fold flap
    fold_flap = [
        (doc_right - fold_size, doc_top),
        (doc_right - fold_size, doc_top + fold_size),
        (doc_right, doc_top + fold_size)
    ]
    draw.polygon(fold_flap, fill=(220, 226, 235, 255))

    # 5. Bold "PDF" Badge / Header inside document
    badge_x0 = doc_pad_x + int(S * 0.06)
    badge_y0 = doc_top + int(S * 0.10)
    badge_x1 = doc_right - int(S * 0.06) - fold_size // 2
    badge_y1 = doc_top + int(S * 0.28)
    badge_r = int(S * 0.035)

    draw.rounded_rectangle(
        [(badge_x0, badge_y0), (badge_x1, badge_y1)],
        radius=badge_r,
        fill=(225, 29, 72, 255) # Modern crimson
    )

    # Draw "PDF" letters inside badge with clean geometry
    # P, D, F letter shapes
    badge_w = badge_x1 - badge_x0
    badge_h = badge_y1 - badge_y0
    char_y0 = badge_y0 + int(badge_h * 0.20)
    char_y1 = badge_y1 - int(badge_h * 0.20)
    char_h = char_y1 - char_y0
    line_th = int(badge_h * 0.16)

    # P
    p_x0 = badge_x0 + int(badge_w * 0.12)
    p_w = int(badge_w * 0.22)
    # Stem
    draw.rectangle([(p_x0, char_y0), (p_x0 + line_th, char_y1)], fill=(255, 255, 255))
    # Loop
    loop_h = char_h // 2 + line_th // 2
    draw.rounded_rectangle(
        [(p_x0, char_y0), (p_x0 + p_w, char_y0 + loop_h)],
        radius=int(line_th * 0.8), fill=(255, 255, 255)
    )
    draw.rounded_rectangle(
        [(p_x0 + line_th, char_y0 + line_th), (p_x0 + p_w - line_th, char_y0 + loop_h - line_th)],
        radius=max(1, int(line_th * 0.3)), fill=(225, 29, 72)
    )

    # D
    d_x0 = p_x0 + p_w + int(badge_w * 0.08)
    d_w = int(badge_w * 0.22)
    draw.rounded_rectangle(
        [(d_x0, char_y0), (d_x0 + d_w, char_y1)],
        radius=int(d_w * 0.45), fill=(255, 255, 255)
    )
    draw.rounded_rectangle(
        [(d_x0 + line_th, char_y0 + line_th), (d_x0 + d_w - line_th, char_y1 - line_th)],
        radius=max(1, int(d_w * 0.25)), fill=(225, 29, 72)
    )

    # F
    f_x0 = d_x0 + d_w + int(badge_w * 0.08)
    f_w = int(badge_w * 0.20)
    draw.rectangle([(f_x0, char_y0), (f_x0 + line_th, char_y1)], fill=(255, 255, 255))
    draw.rectangle([(f_x0, char_y0), (f_x0 + f_w, char_y0 + line_th)], fill=(255, 255, 255))
    draw.rectangle([(f_x0, char_y0 + int(char_h * 0.45)), (f_x0 + int(f_w * 0.85), char_y0 + int(char_h * 0.45) + line_th)], fill=(255, 255, 255))

    # 6. Modern Content Lines on document sheet
    line_x0 = doc_pad_x + int(S * 0.06)
    line_x1 = doc_right - int(S * 0.06)
    line_th2 = int(S * 0.024)
    line_r2 = line_th2 // 2

    for i, length_factor in enumerate([1.0, 0.85, 0.70]):
        cur_y = doc_top + int(S * (0.38 + i * 0.09))
        cur_x1 = line_x0 + int((line_x1 - line_x0) * length_factor)
        color = (195, 205, 220, 255) if i > 0 else (160, 175, 195, 255)
        draw.rounded_rectangle(
            [(line_x0, cur_y), (cur_x1, cur_y + line_th2)],
            radius=line_r2,
            fill=color
        )

    # 7. Sleek Crown / Star Emblem at bottom right of card
    # Downscale from 2048x2048 to master 1024x1024 using Lanczos (super-sampling)
    master_1024 = img.resize((1024, 1024), Image.Resampling.LANCZOS)
    master_1024.save("resources/app_icon.png", format="PNG")
    master_1024.resize((512, 512), Image.Resampling.LANCZOS).save("resources/app_icon_512.png", format="PNG")
    master_1024.resize((256, 256), Image.Resampling.LANCZOS).save("resources/app_icon_256.png", format="PNG")

    # Generate all standard Windows 11 icon sizes for ICO bundle
    ico_sizes = [
        (256, 256),
        (128, 128),
        (96, 96),
        (64, 64),
        (48, 48),
        (40, 40),
        (32, 32),
        (24, 24),
        (20, 20),
        (16, 16),
    ]
    ico_images = [master_1024.resize(sz, Image.Resampling.LANCZOS) for sz in ico_sizes]

    # Save multi-resolution ICO file
    ico_images[0].save(
        "resources/app_icon.ico",
        format="ICO",
        sizes=[(im.width, im.height) for im in ico_images]
    )
    print("Generated ultra high-res app_icon.png and app_icon.ico successfully!")


if __name__ == "__main__":
    create_highres_icon()
