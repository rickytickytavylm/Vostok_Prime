"""Удаляет вшитый шахматный фон у logo_prime.png -> прозрачный webp.

Фон - едва заметная шахматка: светлые клетки ~254 и серые ~243 (клетка ~14px).
Чистый белый (255) есть и в фоне, и в самом лого, поэтому по цвету не разделить.
Но серые клетки (~243) встречаются ТОЛЬКО в фоне. Значит фон = почти-белые
пиксели, находящиеся рядом с серыми клетками; крупное белое лого (далеко от
серых клеток, окружено красным) сохраняется.
"""
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = "assets/logo_prime.png"
OUT = "assets/webp/logo_prime.webp"
D = 18  # радиус «схлопывания» фона к серым клеткам (клетка ~14px)

img = Image.open(SRC).convert("RGB")
a = np.array(img).astype(np.int16)
mx = a.max(axis=2)
mn = a.min(axis=2)
sat = mx - mn

grey = (mn >= 235) & (mx <= 248) & (sat <= 8)   # серые клетки шахматки (только фон)

# «Зона фона» - всё в радиусе D от серых клеток (весь шахматный фон + просветы
# между тонкими красными элементами). Крупное белое лого сюда не попадает.
zone = ndimage.binary_dilation(grey, iterations=D)

# В зоне фона убираем светлое и светлые ореолы (полупрозрачный красный по фону),
# оставляя только насыщенный красный (высокая насыщенность).
lightish = (mn >= 150) & (sat <= 70)
bg = zone & lightish

alpha = np.where(bg, 0, 255).astype(np.uint8)

# подчистить одиночные дырки/шум в альфе
solid = alpha > 0
solid = ndimage.binary_closing(solid, iterations=1)
solid = ndimage.binary_opening(solid, iterations=1)
alpha = np.where(solid, 255, 0).astype(np.uint8)

out = np.dstack([np.array(img), alpha]).astype(np.uint8)

# автообрезка прозрачных полей
ys, xs = np.where(alpha > 0)
if len(xs) and len(ys):
    pad = 8
    x0 = max(int(xs.min()) - pad, 0)
    y0 = max(int(ys.min()) - pad, 0)
    x1 = min(int(xs.max()) + pad + 1, out.shape[1])
    y1 = min(int(ys.max()) + pad + 1, out.shape[0])
    out = out[y0:y1, x0:x1]

Image.fromarray(out, "RGBA").save(OUT, "WEBP", quality=95, method=6)
print("saved", OUT, out.shape)
