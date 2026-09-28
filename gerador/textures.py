import numpy as np, random
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

SRC = Image.open('foto.jpg').convert('RGB')
OUT = 'tex'
FONT = '/System/Library/Fonts/Avenir Next Condensed.ttc'
BLACK = (22, 24, 27)
BLUE = (30, 150, 220)


def rectify(quad, size, bright=1.15):
    """quad: TL, TR, BR, BL no foto -> imagem retangular size (w, h)."""
    w, h = size
    dst = [(0, 0), (w, 0), (w, h), (0, h)]
    A, b = [], []
    for (x, y), (u, v) in zip(dst, quad):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    coef = np.linalg.solve(np.array(A, float), np.array(b, float))
    im = SRC.transform(size, Image.PERSPECTIVE, tuple(coef), Image.BICUBIC, fillcolor=BLACK)
    return ImageEnhance.Brightness(im).enhance(bright)


def splash(d, rnd, cx, cy, spread, n):
    for _ in range(n):
        r = rnd.uniform(2, 9)
        x, y = rnd.gauss(cx, spread), rnd.gauss(cy, spread * 2)
        d.ellipse([x - r, y - r, x + r, y + r], fill=BLUE)


def side(upper, logo_front_right):
    w, h = 580, (820 if upper else 850)
    im = Image.new('RGB', (w, h), BLACK)
    d = ImageDraw.Draw(im)
    rnd = random.Random(7 if upper else 11)
    if upper:
        big = ImageFont.truetype(FONT, 300, index=8)
        mid = ImageFont.truetype(FONT, 150, index=8)
        cx = w * 0.5
        d.text((cx, 330), 'RE', font=big, fill=BLUE, anchor='ms')
        d.text((cx, 470), 'FLOW', font=mid, fill=(240, 240, 240), anchor='ms')
        # grade de ventilação na parte de trás/baixo
        gx = 40 if logo_front_right else w - 190
        for yy in range(560, 760, 14):
            for xx in range(gx, gx + 150, 14):
                d.rectangle([xx, yy, xx + 8, yy + 7], fill=(8, 9, 10))
        splash(d, rnd, w * (0.85 if logo_front_right else 0.15), 760, 25, 40)
    else:
        fx = w * (0.8 if logo_front_right else 0.2)
        d.line([(fx, 0), (fx - 60, h * 0.45)], fill=BLUE, width=22)
        splash(d, rnd, fx, 180, 40, 90)
        splash(d, rnd, fx - 40, 380, 30, 40)
    return im


def plain(size, color=BLACK):
    return Image.new('RGB', size, color)


if __name__ == '__main__':
    import os
    os.makedirs(OUT, exist_ok=True)
    rectify([(335, 12), (712, 19), (725, 745), (350, 818)], (430, 820)).resize((512, 1024)).save(f'{OUT}/frente_sup.jpg', quality=88)
    rectify([(400, 828), (748, 762), (773, 1588), (452, 1665)], (430, 870)).resize((512, 1024)).save(f'{OUT}/frente_inf.jpg', quality=88)
    rectify([(715, 482), (800, 468), (826, 682), (745, 702)], (90, 200), 1.05).resize((128, 256)).save(f'{OUT}/maquininha.jpg', quality=90)
    rectify([(688, 15), (856, 27), (859, 338), (695, 352)], (200, 360), 1.05).resize((256, 512)).save(f'{OUT}/placa.jpg', quality=90)
    side(True, True).resize((512, 1024)).save(f'{OUT}/lado_sup_esq.jpg', quality=88)
    side(True, False).resize((512, 1024)).save(f'{OUT}/lado_sup_dir.jpg', quality=88)
    side(False, True).resize((512, 1024)).save(f'{OUT}/lado_inf_esq.jpg', quality=88)
    side(False, False).resize((512, 1024)).save(f'{OUT}/lado_inf_dir.jpg', quality=88)
