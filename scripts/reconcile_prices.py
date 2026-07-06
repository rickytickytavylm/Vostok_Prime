#!/usr/bin/env python3
"""Сверка прайса с нашими данными: что получило цену, что нет, чего у нас нет."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from build_catalog import CAKE_META  # noqa: E402
from price_list import normalize, parse, weights_for_title, TITLE_ALIASES  # noqa: E402


def main() -> int:
    table = parse()
    used_keys: set[str] = set()

    matched: list[str] = []
    no_price: list[str] = []

    for slug, meta in CAKE_META.items():
        w = weights_for_title(meta["title"], table)
        if w:
            matched.append(f"{meta['title']}: " + ", ".join(f"{x['label']} — {x['price']}" for x in w))
            norm = TITLE_ALIASES.get(normalize(meta["title"]), normalize(meta["title"]))
            used_keys.add(norm)
        else:
            no_price.append(meta["title"])

    extra = sorted(set(table) - used_keys)

    lines = [
        "# Сверка прайса с данными сайта",
        "",
        f"- Тортов у нас: {len(CAKE_META)}",
        f"- Позиций в прайсе: {len(table)}",
        f"- Получили реальную цену: {len(matched)}",
        f"- Без цены (нет в прайсе): {len(no_price)}",
        f"- В прайсе, но НЕТ у нас на сайте: {len(extra)}",
        "",
        "## Наши торты без цены в прайсе",
        "",
    ]
    for t in no_price:
        lines.append(f"- {t}")
    lines.append("")
    lines.append("## Есть в прайсе, но отсутствуют у нас (потенциально добавить)")
    lines.append("")
    for k in extra:
        ws = ", ".join(f"{e['label']} — {e['price']}" for e in table[k])
        lines.append(f"- {k} — {ws}")
    lines.append("")

    (ROOT / "data" / "PRICES-RECONCILE.md").write_text("\n".join(lines), encoding="utf-8")

    print("=" * 50)
    print(f"Тортов у нас:            {len(CAKE_META)}")
    print(f"Позиций в прайсе:        {len(table)}")
    print(f"Получили цену:           {len(matched)}")
    print(f"Без цены (нет в прайсе): {len(no_price)} -> {', '.join(no_price) if no_price else '—'}")
    print(f"В прайсе, нет у нас:     {len(extra)}")
    print("=" * 50)
    print("Отчёт: data/PRICES-RECONCILE.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
