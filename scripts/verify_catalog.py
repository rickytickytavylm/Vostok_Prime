#!/usr/bin/env python3
"""Сверка: new cakes <-> webp <-> CAKE_META. Выявляет все расхождения."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from build_catalog import (  # noqa: E402
    CAKE_META,
    NEW_CAKES,
    WEBP_ROOT,
    parse_new_cake_name_fixed,
)

CLASSIC_SLUGS = [s for s, m in CAKE_META.items() if m.get("section") == "classic"]

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def main() -> int:
    # 1. Что распарсилось из new cakes
    new_files: dict[str, dict[str, str]] = {}
    new_unmapped: list[str] = []
    for src in sorted(NEW_CAKES.iterdir()):
        if src.suffix.lower() not in IMAGE_EXTS:
            continue
        parsed = parse_new_cake_name_fixed(src.name)
        if not parsed:
            new_unmapped.append(src.name)
            continue
        slug, view = parsed
        new_files.setdefault(slug, {})[view] = src.name

    # 2. Реальные webp файлы
    webp_dir = WEBP_ROOT / "cakes"
    webp_slugs: dict[str, set[str]] = {}
    for f in sorted(webp_dir.glob("*.webp")):
        stem = f.stem
        if stem.endswith("-whole"):
            webp_slugs.setdefault(stem[:-6], set()).add("whole")
        elif stem.endswith("-cut"):
            webp_slugs.setdefault(stem[:-4], set()).add("cut")

    meta_slugs = set(CAKE_META.keys())
    new_slugs = set(new_files.keys())
    webp_keys = set(webp_slugs.keys())

    print("=" * 60)
    print(f"Файлов в new cakes:     {sum(len(v) for v in new_files.values()) + len(new_unmapped)}")
    print(f"Тортов из new cakes:    {len(new_slugs)}")
    print(f"Тортов в CAKE_META:     {len(meta_slugs)}")
    print(f"Тортов c webp:          {len(webp_keys)}")
    print("=" * 60)

    if new_unmapped:
        print("\n[!] НЕ РАСПОЗНАНЫ имена файлов:")
        for n in new_unmapped:
            print(f"    {n}")
    else:
        print("\n[OK] Все имена файлов распознаны.")

    # new cakes без записи в CAKE_META
    orphan_new = new_slugs - meta_slugs
    if orphan_new:
        print("\n[!] Есть фото в new cakes, но НЕТ в CAKE_META (не попадут на сайт):")
        for s in sorted(orphan_new):
            print(f"    {s}  <- {new_files[s]}")
    else:
        print("\n[OK] Все торты из new cakes есть в CAKE_META.")

    # CAKE_META без фото вообще
    no_photo = sorted(s for s in meta_slugs if s not in webp_keys)
    if no_photo:
        print(f"\n[i] В CAKE_META без фото ({len(no_photo)}):")
        for s in no_photo:
            print(f"    {s}  ({CAKE_META[s]['title']})")

    # неполные пары
    print("\n[i] Неполные пары (есть только один ракурс):")
    any_partial = False
    for s in sorted(webp_keys):
        views = webp_slugs[s]
        if views != {"whole", "cut"}:
            any_partial = True
            print(f"    {s}: только {', '.join(views)}")
    if not any_partial:
        print("    нет — у всех есть оба ракурса")

    # webp без CAKE_META
    orphan_webp = webp_keys - meta_slugs
    if orphan_webp:
        print("\n[!] WebP-файлы без записи в CAKE_META:")
        for s in sorted(orphan_webp):
            print(f"    {s}")

    # Классические из списка заказчика
    print("\n" + "=" * 60)
    print("КЛАССИЧЕСКИЕ (список заказчика, 13 шт):")
    for s in CLASSIC_SLUGS:
        has = "фото есть" if s in webp_keys else "БЕЗ ФОТО"
        print(f"    {CAKE_META[s]['title']:<14} {has}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
