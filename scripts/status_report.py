#!/usr/bin/env python3
"""Единый чек-лист статуса по всей продукции. Что есть / чего не хватает."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from build_catalog import (  # noqa: E402
    CAKE_META,
    COOKIES,
    PASTRIES,
    SECTIONS,
    build_products,
)

# Описания, которые реально дала заказчица
REAL_DESC_SLUGS = {s for s, m in CAKE_META.items() if m.get("desc_source") == "mom"}


def load_catalog() -> dict:
    path = ROOT / "data" / "product-images-catalog.json"
    if not path.exists():
        return {"cakes": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def photo_status(images: dict) -> str:
    has_w = "whole" in images
    has_c = "cut" in images
    if has_w and has_c:
        return "OK (общий + разрез)"
    if has_w:
        return "нужен РАЗРЕЗ"
    if has_c:
        return "нужен ОБЩИЙ ВИД"
    return "НЕТ ФОТО (нужны оба)"


def main() -> int:
    catalog = load_catalog()
    cakes_img = catalog.get("cakes", {})
    products = build_products(catalog)

    lines: list[str] = [
        "# СТАТУС ПРОЕКТА — что готово и что нужно",
        "",
        "Единый источник правды. Генерится: `python scripts/status_report.py`.",
        "",
        "Легенда: **Фото** — есть ли снимки; **Описание** — `ваше` (от заказчицы) "
        "или `заглушка` (написал ассистент, нужно заменить); **Цена** — реальная или «уточняйте».",
        "",
    ]

    need_photo: list[str] = []
    need_desc: list[str] = []
    need_price: list[str] = []

    label_by_id = {s["id"]: s["label"] for s in SECTIONS}

    for section in SECTIONS:
        sid = section["id"]
        items = products.get(sid, [])
        if not items:
            continue
        lines.append(f"## {section['label']} ({len(items)})")
        lines.append("")
        lines.append("| Торт | Фото | Описание | Цена |")
        lines.append("|------|------|----------|------|")
        for it in items:
            slug = it.get("slug")
            if sid in ("pastries", "cookies") or not slug:
                photo = "—"
                desc = "заглушка"
            else:
                photo = photo_status(cakes_img.get(slug, {}).get("images", {}))
                src = CAKE_META.get(slug, {}).get("desc_source")
                desc = {"mom": "ваше", "pending": "ждёт описания", "placeholder": "заглушка"}.get(src, "заглушка")
                if "НЕТ" in photo or "нужен" in photo:
                    need_photo.append(f"{it['title']} ({section['label']}) — {photo}")
                if desc != "ваше":
                    need_desc.append(f"{it['title']} ({section['label']}) — {desc}")

            prices = [w["price"] for w in it["weights"]]
            real_price = any(p != "уточняйте" for p in prices)
            price = "есть" if real_price else "уточняйте"
            if not real_price and slug:
                need_price.append(f"{it['title']} ({section['label']})")

            lines.append(f"| {it['title']} | {photo} | {desc} | {price} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("# ЧТО НУЖНО СОБРАТЬ (по приоритету)")
    lines.append("")
    lines.append(f"## 1. Фото — {len(need_photo)} позиций")
    lines.append("")
    for n in need_photo:
        lines.append(f"- [ ] {n}")
    lines.append("")
    lines.append(f"## 2. Настоящие описания вместо заглушек — {len(need_desc)} позиций")
    lines.append("")
    for n in need_desc:
        lines.append(f"- [ ] {n}")
    lines.append("")
    lines.append(f"## 3. Реальные цены/фасовки — {len(need_price)} позиций")
    lines.append("")
    for n in need_price:
        lines.append(f"- [ ] {n}")
    lines.append("")

    path = ROOT / "data" / "STATUS.md"
    path.write_text("\n".join(lines), encoding="utf-8")

    print("СВОДКА")
    print("=" * 50)
    total = sum(len(products[s["id"]]) for s in SECTIONS)
    print(f"Всего позиций:           {total}")
    print(f"Нужно фото:              {len(need_photo)}")
    print(f"Нужно настоящих описаний: {len(need_desc)}")
    print(f"Нужно реальных цен:       {len(need_price)}")
    print("=" * 50)
    print(f"Файл: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
