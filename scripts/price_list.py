#!/usr/bin/env python3
"""Парсер официального прайса -> веса и цены по названию торта."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "price-list-raw.txt"

# Наше название (как в CAKE_META) -> базовое имя в прайсе (если отличается)
TITLE_ALIASES = {
    "земляничный десерт": "десерт земляничный",
}

_LINE = re.compile(r"^(.*?)\s+([\d]+(?:[.,]\d+)?)\s*(?:кг)?\.?\s*\t\s*([\d.,]+)\s*$")


def normalize(name: str) -> str:
    name = name.strip().lower().replace("ё", "е")
    name = re.sub(r"«|»|\"", "", name)
    name = re.sub(r"\s*\(.*?\)\s*", " ", name)  # убрать (вкус)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _fmt_weight(num: float) -> str:
    if abs(num - round(num)) < 1e-9:
        return f"{int(round(num))} кг"
    return f"{('%g' % num).replace('.', ',')} кг"


def _fmt_price(value: float) -> str:
    rub = int(round(value))
    return f"{rub:,}".replace(",", " ") + " ₽"


def parse() -> dict[str, list[dict]]:
    """norm_name -> [{'num': float, 'label': str, 'price': str}] (по возрастанию веса)."""
    out: dict[str, list[dict]] = {}
    if not RAW.exists():
        return out
    for line in RAW.read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or line.startswith("##"):
            continue
        m = _LINE.match(line)
        if not m:
            continue
        raw_name, weight_raw, price_raw = m.groups()
        num = float(weight_raw.replace(",", "."))
        price = float(price_raw.replace(",", ""))
        key = normalize(raw_name)
        entry = {"num": num, "label": _fmt_weight(num), "price": _fmt_price(price)}
        bucket = out.setdefault(key, [])
        if not any(abs(e["num"] - num) < 1e-9 for e in bucket):
            bucket.append(entry)
    for bucket in out.values():
        bucket.sort(key=lambda e: e["num"])
    return out


def weights_for_title(title: str, table: dict[str, list[dict]] | None = None) -> list[dict] | None:
    table = table if table is not None else parse()
    norm = normalize(title)
    norm = TITLE_ALIASES.get(norm, norm)
    bucket = table.get(norm)
    if not bucket:
        return None
    return [{"label": e["label"], "price": e["price"]} for e in bucket]


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    t = parse()
    print(f"Позиций в прайсе: {len(t)}")
    for name in sorted(t)[:10]:
        print(name, t[name])
