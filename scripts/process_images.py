#!/usr/bin/env python3
"""Convert assets to WebP, latin filenames, build product image catalog."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
WEBP_ROOT = ASSETS / "webp"
NEW_CAKES = ASSETS / "new cakes"
OLD_CAKES = ASSETS / "cakes"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# Cyrillic product name -> latin slug
SLUG_MAP = {
    "черный-люкс": "chernyy-lyuks",
    "чёрный-люкс": "chernyy-lyuks",
    "черный люкс": "chernyy-lyuks",
    "чародейка": "charodeyka",
    "шоколадная-девочка": "shokoladnaya-devochka",
    "шоколадная девочка": "shokoladnaya-devochka",
    "земляничный-десерт": "zemlenichnyy-desert",
    "земляничный десерт": "zemlenichnyy-desert",
    "земленичный-десерт": "zemlenichnyy-desert",
    "земленичный десерт": "zemlenichnyy-desert",
    "с-черносливом": "s-chersnoslivym",
    "с-чёрносливом": "s-chersnoslivym",
    "с-черсносливым": "s-chersnoslivym",
    "прага": "praga",
    "тирамису": "tiramisu",
    "вишневый": "vishnevyy",
    "вишня-со-сливками": "vishnya-so-slivkami",
    "восточная-сказка": "vostochnaya-skazka",
    "восточная сказка": "vostochnaya-skazka",
    "парижские-тайны": "parizhskie-tayny",
    "парижские тайны": "parizhskie-tayny",
    "оригинальный": "originalnyy",
    "домашний": "domashniy",
    "нежность": "nezhnost",
    "рафаэлло": "rafaello",
    "каприз": "kapriz",
    "лавандовый": "lavandovyy",
    "цветы": "tsvety",
    "крем-брюле": "krem-bryule",
    "клубничка": "klubnichka",
    "север": "sever",
    "флирт": "flirt",
    "к-чаю": "k-chayu",
    "к чаю": "k-chayu",
    "ежик": "yozhik",
    "ёжик": "yozhik",
    "кармен": "karmen",
    "медовик": "medovik",
    "сакура": "sakura",
    "соблазн": "soblazn",
    "любимый": "lyubimyy",
    "московский": "moskovskiy",
    "продавец": "prodavets",
    "продавец": "prodavets",
    "фантазия": "fantaziya",
    "киевский": "kievskiy",
    "графский": "grafskiy",
    "трюфельный": "tryufelnyy",
    "чизкейк": "chizkeyk",
    "сникерс": "snikers",
    "изобилие": "izobilie",
    "полет": "polet",
    "полёт": "polet",
    "королевский": "korolevskiy",
    "гурмэ": "gurme",
    "элитный": "elitnyy",
    "наполеон": "napoleon",
    "медовичок": "medovichok",
    "медовичек": "medovichok",
    "шоколадно-ореховый": "shokoladno-orehovyy",
    "подарочный": "podarochnyy",
    "зимняя-вишня": "zimnyaya-vishnya",
    "зимняя вишня": "zimnyaya-vishnya",
    "забайкальская-птичка": "zabaykalskaya-ptichka",
    "забайкальская птичка": "zabaykalskaya-ptichka",
    "клубничное-чудо": "klubnichnoe-chudo",
    "клубничное чудо": "klubnichnoe-chudo",
    "эскимо": "eskimo",
    "молочная-девочка": "molochnaya-devochka",
    "молочная девочка": "molochnaya-devochka",
    "росинка": "rosinka",
    "шанхай": "shanhay",
    "чернослив-в-шоколаде": "chernosliv-v-shokolade",
    "чернослив в шоколаде": "chernosliv-v-shokolade",
    "сакура": "sakura",
    "идиллия": "idilliya",
    "медовый": "medovyy",
    "мокко": "mokko",
    "гороскоп": "goroskop",
    "идиллия": "idilliya",
    "курский": "kurskiy",
    "лакомка": "lakomka",
    "праздничный": "prazdnichnyy",
    "три-желания": "tri-zhelaniya",
    "творожный-счастливчик": "tvorozhnyy-schastlivchik",
    "царский": "tsarskiy",
    "фиеста": "fiesta",
    "черемуховый": "cheremukhovyy",
    "черёмуховый": "cheremukhovyy",
}

# Old latin files in assets/cakes -> slug + view
OLD_FILE_MAP = {
    "black_lux_1": ("chernyy-lyuks", "whole"),
    "black_lux_2": ("chernyy-lyuks", "cut"),
    "magic_1": ("charodeyka", "whole"),
    "magic_2": ("charodeyka", "cut"),
    "choko_girl_1": ("shokoladnaya-devochka", "whole"),
    "choko_girl_2": ("shokoladnaya-devochka", "cut"),
    "cake_with_prunes1": ("s-chersnoslivym", "whole"),
    "cake_with_prunes2": ("s-chersnoslivym", "cut"),
    "praga_1": ("praga", "whole"),
    "praga_2": ("praga", "cut"),
    "tiramisu_1": ("tiramisu", "whole"),
    "tiramisu_2": ("tiramisu", "cut"),
    "chery_cake_1": ("vishnevyy", "whole"),
    "chery_cake_2": ("vishnevyy", "cut"),
    "strawberry_1": ("zemlenichnyy-desert", "whole"),
    "strawberry_2": ("zemlenichnyy-desert", "cut"),
    "east_dream_1": ("vostochnaya-skazka", "whole"),
    "east_dream_2": ("vostochnaya-skazka", "cut"),
    "paris_enigma_1": ("parizhskie-tayny", "whole"),
    "paris_enigma_2": ("parizhskie-tayny", "cut"),
    "original_1": ("originalnyy", "whole"),
    "original_2": ("originalnyy", "cut"),
    "background1": ("_background", "1"),
    "background2": ("_background", "2"),
    "background3": ("_background", "3"),
    "background4": ("_background", "4"),
    "vostok_promo": ("_promo", "hero"),
}

VIEW_WHOLE = {"общий", "общий вид", "whole", "1"}
VIEW_CUT = {"разрез", "разрезjpg", "cut", "2"}


def slugify(text: str) -> str:
    text = text.strip().lower().replace("_", "-")
    text = text.replace("ё", "е")
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9\-а-я]+", "", text, flags=re.IGNORECASE)
    if text in SLUG_MAP:
        return SLUG_MAP[text]
    # translit rough
    out = []
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ж": "zh", "з": "z",
        "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
        "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
        "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    for ch in text:
        if ch in table:
            out.append(table[ch])
        elif re.match(r"[a-z0-9\-]", ch):
            out.append(ch)
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug or "image"


def parse_new_cake_name(filename: str) -> tuple[str, str] | None:
    stem = Path(filename).stem.lower().replace("ё", "е")
    stem = re.sub(r"\.(jpg|jpeg|png)$", "", stem, flags=re.I)
    # typos / alternate patterns
    stem = stem.replace("рразрез", "разрез")
    if " " in stem and "-" not in stem:
        parts = stem.rsplit(" ", 1)
        if len(parts) == 2 and parts[1] in VIEW_CUT | VIEW_WHOLE or parts[1].startswith("разре") or parts[1].startswith("общ"):
            stem = f"{parts[0]}-{parts[1]}"
    if "-" not in stem:
        return None
    name, view_raw = stem.rsplit("-", 1)
    view_raw = view_raw.replace("jpg", "").strip()
    if view_raw in VIEW_WHOLE or view_raw.startswith("общ"):
        view = "whole"
    elif view_raw in VIEW_CUT or view_raw.startswith("разре"):
        view = "cut"
    else:
        return None
    slug = SLUG_MAP.get(name, slugify(name))
    return slug, view


def ffmpeg_to_webp(src: Path, dst: Path, quality: int = 82) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src),
        "-vf", "scale=iw:ih:flags=lanczos",
        "-c:v", "libwebp",
        "-quality", str(quality),
        "-preset", "picture",
        str(dst),
    ]
    subprocess.run(cmd, check=True)


def rel_webp(path: Path) -> str:
    return "./" + path.relative_to(ROOT).as_posix()


def main() -> int:
    catalog: dict = {
        "generated_by": "scripts/process_images.py",
        "webp_root": "assets/webp",
        "cakes": {},
        "other": [],
        "unmapped_sources": [],
    }

    jobs: list[tuple[Path, Path, str, str, str]] = []

    # --- new cakes (cyrillic names) ---
    if NEW_CAKES.exists():
        for src in sorted(NEW_CAKES.iterdir()):
            if src.suffix.lower() not in IMAGE_EXTS:
                continue
            parsed = parse_new_cake_name(src.name)
            if not parsed:
                catalog["unmapped_sources"].append(str(src.relative_to(ROOT)))
                continue
            slug, view = parsed
            dst = WEBP_ROOT / "cakes" / f"{slug}-{view}.webp"
            jobs.append((src, dst, slug, view, "new"))
    else:
        print(f"WARN: missing folder {NEW_CAKES}")

    # --- old cakes ---
    if OLD_CAKES.exists():
        for src in sorted(OLD_CAKES.iterdir()):
            if src.suffix.lower() not in IMAGE_EXTS:
                continue
            stem = src.stem
            if stem in OLD_FILE_MAP:
                slug, view = OLD_FILE_MAP[stem]
                if slug.startswith("_"):
                    sub = "misc" if slug == "_promo" else "backgrounds"
                    dst = WEBP_ROOT / sub / f"{slugify(stem)}.webp"
                else:
                    dst = WEBP_ROOT / "cakes" / f"{slug}-{view}.webp"
                jobs.append((src, dst, slug, view, "old"))
            else:
                catalog["unmapped_sources"].append(str(src.relative_to(ROOT)))

    # --- hero ---
    hero = ASSETS / "hero.png"
    if hero.exists():
        jobs.append((hero, WEBP_ROOT / "hero.webp", "hero", "whole", "hero"))

    # --- berries (already latin) ---
    berries = ASSETS / "berries"
    if berries.exists():
        for src in sorted(berries.iterdir()):
            if src.suffix.lower() not in IMAGE_EXTS:
                continue
            dst = WEBP_ROOT / "berries" / f"{slugify(src.stem)}.webp"
            jobs.append((src, dst, src.stem, "whole", "berry"))

    print(f"Converting {len(jobs)} images to WebP...")
    for i, (src, dst, slug, view, kind) in enumerate(jobs, 1):
        print(f"[{i}/{len(jobs)}] {src.name} -> {dst.relative_to(ROOT)}")
        try:
            ffmpeg_to_webp(src, dst)
        except subprocess.CalledProcessError as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            catalog["unmapped_sources"].append(f"FAILED:{src.relative_to(ROOT)}")
            continue

        if kind in {"new", "old"} and not slug.startswith("_"):
            cake = catalog["cakes"].setdefault(slug, {
                "slug": slug,
                "images": {},
                "sources": [],
            })
            cake["images"][view] = rel_webp(dst)
            cake["sources"].append({
                "file": str(src.relative_to(ROOT)),
                "view": view,
                "origin": kind,
            })
        else:
            catalog["other"].append({
                "slug": slug,
                "view": view,
                "webp": rel_webp(dst),
                "source": str(src.relative_to(ROOT)),
                "kind": kind,
            })

    # Product descriptions for AI doc
    classic_descriptions = {
        "domashniy": "Классический белый бисквит в сочетании со взбитыми сливками.",
        "nezhnost": "Классический белый бисквит пропитан сахарным сиропом в сочетании с ванильно-сливочным кремом.",
        "rafaello": "Классический белый бисквит пропитан сиропом «Миндаль», прослоен взбитыми сливками с варёным сгущённым молоком. Оформлен кокосовой стружкой и вафельными шариками.",
        "kapriz": "Классический белый бисквит прослоен взбитыми сливками с клубничным вкусом. Оформлен воздушным рисом.",
        "lavandovyy": "Лавандовый бисквит прослоен взбитыми сливками и конфитюром «Черника».",
        "tsvety": "Классический белый бисквит в сочетании с яблочным повидлом и взбитыми сливками.",
        "krem-bryule": "Классический белый бисквит пропитан сахарным сиропом, прослоен сливочным кремом на основе варёного сгущённого молока.",
        "klubnichka": "Классический белый бисквит прослоен ванильно-сливочным кремом.",
        "sever": "Классический белый бисквит пропитан сиропом с десертным вином, прослоен фруктовым повидлом. Оформлен белковым кремом.",
        "flirt": "Классический белый бисквит прослоен взбитыми сливками. Оформлен кокосовой стружкой.",
        "k-chayu": "Классический шоколадный бисквит в сочетании с ванильно-сливочным кремом.",
        "yozhik": "Бисквитная крошка с добавлением какао и ванильно-сливочного крема.",
        "karmen": "Классический шоколадный бисквит в сочетании с шоколадно-сливочным кремом.",
    }

    site_products = {
        "chernyy-lyuks": {"title": "Чёрный Люкс", "category": "cakes"},
        "charodeyka": {"title": "Чародейка", "category": "cakes"},
        "shokoladnaya-devochka": {"title": "Шоколадная девочка", "category": "cakes"},
        "tort-s-chernoslivom": {"title": "Торт с черносливом", "category": "cakes"},
        "praga": {"title": "Прага", "category": "cakes"},
        "tiramisu": {"title": "Тирамису", "category": "cakes"},
        "vishnevyy": {"title": "Вишневый", "category": "cakes"},
        "zemlyanichnyy-desert": {"title": "Земляничный десерт", "category": "cakes"},
        "vostochnaya-skazka": {"title": "Восточная сказка", "category": "cakes"},
        "parizhskie-tayny": {"title": "Парижские тайны", "category": "cakes"},
        "originalnyy": {"title": "Оригинальный", "category": "cakes"},
    }

    for slug, meta in site_products.items():
        if slug in catalog["cakes"]:
            catalog["cakes"][slug].update(meta)
    for slug, desc in classic_descriptions.items():
        if slug in catalog["cakes"]:
            catalog["cakes"][slug]["description"] = desc
            catalog["cakes"][slug].setdefault("title", slug)
            catalog["cakes"][slug].setdefault("category", "cakes")

    out_json = ROOT / "data" / "product-images-catalog.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown for AI
    lines = [
        "# Каталог изображений продукции — фабрика «Восток»",
        "",
        "Автогенерация из `scripts/process_images.py`. Формат имён: `{slug}-whole.webp` / `{slug}-cut.webp`.",
        "",
        "## Торты с фото",
        "",
    ]
    for slug in sorted(catalog["cakes"]):
        c = catalog["cakes"][slug]
        title = c.get("title", slug)
        lines.append(f"### {title} (`{slug}`)")
        if c.get("description"):
            lines.append(f"- **Описание:** {c['description']}")
        imgs = c.get("images", {})
        if "whole" in imgs:
            lines.append(f"- **Общий вид:** `{imgs['whole']}`")
        if "cut" in imgs:
            lines.append(f"- **Разрез:** `{imgs['cut']}`")
        if c.get("sources"):
            lines.append("- **Исходники:**")
            for s in c["sources"]:
                lines.append(f"  - `{s['file']}` ({s['view']}, {s['origin']})")
        lines.append("")

    if catalog["unmapped_sources"]:
        lines.extend(["## Не сопоставлено автоматически", ""])
        for u in catalog["unmapped_sources"]:
            lines.append(f"- `{u}`")
        lines.append("")

    out_md = ROOT / "data" / "PRODUCT-IMAGES.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"\nDone. Catalog: {out_json}")
    print(f"Doc: {out_md}")
    print(f"Cakes mapped: {len(catalog['cakes'])}")
    print(f"Unmapped: {len(catalog['unmapped_sources'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
