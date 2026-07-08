#!/usr/bin/env python3
"""Build product catalog: images -> webp + products-data.js for the site.

Структура и описания — по письмам заказчицы (Лилия). Единый источник правды.
desc_source: "mom" — текст заказчицы; "placeholder" — временная заглушка;
"pending" — ждём описание из будущих писем.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from process_images import (  # noqa: E402
    ASSETS,
    IMAGE_EXTS,
    NEW_CAKES,
    OLD_CAKES,
    OLD_FILE_MAP,
    ROOT as IMG_ROOT,
    WEBP_ROOT,
    ffmpeg_to_webp,
    parse_new_cake_name,
    rel_webp,
    slugify,
)
from price_list import parse as price_parse  # noqa: E402
from price_list import weights_for_title as price_weights_for_title  # noqa: E402

# Вторая партия фото (кириллица, письма Leo от 30.06–01.07).
# Явная карта имя_файла -> (slug, view): в именах опечатки и разные суффиксы,
# поэтому надёжнее сопоставить руками, чем парсером.
NEW_CAKES2 = ASSETS / "new cakes2"
NEW_CAKES2_MAP: dict[str, tuple[str, str]] = {
    "клубничное_чудо_общий.jpg": ("klubnichnoe-chudo", "whole"),
    "краасный_бархат_разрез.jpg": ("krasnyy-barhat", "cut"),
    "красный-бархат_общий.jpg": ("krasnyy-barhat", "whole"),
    "лакомка_общийjpg.jpg": ("lakomka", "whole"),
    "лакоммка_разрез.jpg": ("lakomka", "cut"),
    "пирожное_графские_развалины.jpg": ("grafskie-razvaliny", "whole"),
    "пирожное_кольцо_заварное.jpg": ("kolco-zavarnoe", "whole"),
    "Пирожное_корзиночка.jpg": ("korzinochka", "whole"),
    "пирожное_эклеры.jpg": ("eklery", "whole"),
    "пирожные_бисквитно_кремовые.jpg": ("biskvitno-kremovoe", "whole"),
    "пирожные_бисквитно_кремовые_с_суфле.jpg": ("biskvitno-kremovoe-sufle", "whole"),
    "полет_премимум_общий.jpg": ("polet-premium", "whole"),
    "полет_с_варенным_сгущенным_молоком_общий_0.5.jpg": ("polet-varenka", "whole"),
    "полет_с_варенным_сгущенным_молоком_общий_1.0кг.jpg": ("polet-varenka", "whole"),
    "полет_с_кедровым_орехом_общий.jpg": ("polet-kedrovyy", "whole"),
    "полет_со_сливочным_кремом_0.5.jpg": ("polet-slivochnyy", "whole"),
    "полет_со_со_сливочным_кремом_1.0кг.jpg": ("polet-slivochnyy", "whole"),
    "славутич_общий.jpg": ("slavutich", "whole"),
    "торт_суфле_забайкальская_птичка.jpg": ("zabaykalskaya-ptichka", "whole"),
    "фисташковый_общий.jpg": ("fistashkovyy", "whole"),
    "царский_банановый_общий.jpg": ("tsarskiy-bananovyy", "whole"),
    "царский_общий.jpg": ("tsarskiy", "whole"),
    "чернослив_в_шоколаде_общий.jpg": ("chernosliv-v-shokolade", "whole"),
    "эльбрус_оббщий.jpg": ("elbrus", "whole"),
}

# --- разделы на сайте (мамина структура) ---
SECTIONS = [
    {"id": "classic", "label": "Классические"},
    {"id": "homemade", "label": "Домашние"},
    {"id": "other", "label": "Другие"},
    {"id": "pastries", "label": "Пирожные"},
    {"id": "cookies", "label": "Печенье"},
]

# Подразделы «Домашних» по бисквитной основе (без подписи, просто порядок)
BISCUIT_LABEL = {
    "a": "бисквит на сметане и сгущённом молоке",
    "b": "бисквит на сметане",
    "v": "бисквит на сгущённом молоке",
    "g": "масляный бисквит",
}
BISCUIT_ORDER = {"a": 0, "b": 1, "v": 2, "g": 3, None: 9}

# Торты: порядок вывода = порядок в этом словаре.
# weights: реальные цены оставлены со старого сайта, остальные — «уточняйте».
CAKE_META: dict[str, dict] = {
    # ========== КЛАССИЧЕСКИЕ (письмо 21 мая, 13 шт) ==========
    "domashniy": {"title": "Домашний", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит в сочетании со взбитыми сливками."},
    "nezhnost": {"title": "Нежность", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит пропитан сахарным сиропом в сочетании с ванильно-сливочным кремом."},
    "rafaello": {"title": "Рафаэлло", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит пропитан сиропом «Миндаль», прослоен взбитыми сливками с варёным сгущённым молоком. Оформлен кокосовой стружкой и вафельными шариками."},
    "kapriz": {"title": "Каприз", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит прослоен взбитыми сливками с клубничным вкусом. Оформлен воздушным рисом."},
    "lavandovyy": {"title": "Лавандовый", "section": "classic", "desc_source": "mom",
        "description": "Лавандовый бисквит прослоен взбитыми сливками и конфитюром «Черника»."},
    "tsvety": {"title": "Цветы", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит в сочетании с яблочным повидлом и взбитыми сливками."},
    "krem-bryule": {"title": "Крем-брюле", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит пропитан сахарным сиропом, прослоен сливочным кремом на основе варёного сгущённого молока."},
    "klubnichka": {"title": "Клубничка", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит прослоен ванильно-сливочным кремом."},
    "sever": {"title": "Север", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит пропитан сиропом с десертным вином, прослоен фруктовым повидлом. Оформлен белковым кремом."},
    "flirt": {"title": "Флирт", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит прослоен взбитыми сливками. Оформлен кокосовой стружкой."},
    "k-chayu": {"title": "К чаю", "section": "classic", "desc_source": "mom",
        "description": "Классический шоколадный бисквит в сочетании с ванильно-сливочным кремом."},
    "yozhik": {"title": "Ёжик", "section": "classic", "desc_source": "mom",
        "description": "Бисквитная крошка с добавлением какао и ванильно-сливочного крема."},
    "karmen": {"title": "Кармен", "section": "classic", "desc_source": "mom",
        "description": "Классический шоколадный бисквит в сочетании с шоколадно-сливочным кремом."},
    # ========== КЛАССИЧЕСКИЕ (письмо 28 мая, 12 шт) ==========
    "shokoladno-orehovyy": {"title": "Шоколадно-ореховый", "section": "classic", "desc_source": "mom",
        "description": "Классический бисквит на варёном сгущённом молоке прослоен взбитыми сливками с варёным сгущённым молоком, арахисом и солёной карамелью."},
    "podarochnyy": {"title": "Подарочный", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит прослоен сливочным кремом на основе варёного сгущённого молока. Оформлен жареным арахисом."},
    "goroskop": {"title": "Гороскоп", "section": "classic", "desc_source": "mom",
        "description": "Песочные коржи в сочетании с шоколадным сливочно-белковым кремом."},
    "lyubimyy": {"title": "Любимый", "section": "classic", "desc_source": "mom",
        "description": "Песочные коржи в сочетании со сливочным кремом на основе варёного сгущённого молока."},
    "tvorozhnyy-schastlivchik": {"title": "Творожный счастливчик", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит с натуральным творогом в сочетании со взбитыми сливками."},
    "zimnyaya-vishnya": {"title": "Зимняя вишня", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит с натуральным творогом в сочетании с белковым кремом и кусочками вишни."},
    "medovyy": {"title": "Медовый", "section": "classic", "desc_source": "mom",
        "description": "Коржи с натуральным мёдом прослоены сливочно-йогуртовым кремом."},
    "medovichok": {"title": "Медовичок", "section": "classic", "desc_source": "mom",
        "description": "Коржи с натуральным мёдом прослоены варёным сгущённым молоком."},
    "fiesta": {"title": "Фиеста", "section": "classic", "desc_source": "mom",
        "description": "Коржи с натуральным мёдом прослоены сливочным кремом на основе варёного сгущённого молока. Оформлен белковым кремом."},
    "korolevskiy": {"title": "Королевский", "section": "classic", "desc_source": "mom",
        "description": "Классический белый бисквит прослоен взбитыми сливками с кусочками фруктов и грецким орехом."},
    "napoleon": {"title": "Наполеон", "section": "classic", "desc_source": "mom",
        "description": "Тонкие коржи слоёного теста прослоены сгущённым молоком."},
    "zabaykalskaya-ptichka": {"title": "Забайкальская птичка", "section": "classic", "desc_source": "mom",
        "description": "Ванильно-сливочное суфле в сочетании с классическим белым бисквитом. Оформлен шоколадной глазурью."},

    # ========== ДОМАШНИЕ — а) бисквит на сметане и сгущённом молоке ==========
    "vostochnaya-skazka": {"title": "Восточная сказка", "section": "homemade", "biscuit": "a", "desc_source": "mom",
        "description": "Слои шоколадного и белого бисквита на сметане и сгущённом молоке прослоены йогуртовым кремом и клубничным конфитюром."},
    "originalnyy": {"title": "Оригинальный", "section": "homemade", "biscuit": "a", "desc_source": "mom",
        "description": "Слои шоколадного и белого бисквита на сметане и сгущённом молоке прослоены сметанным кремом."},
    "mokko": {"title": "Мокко", "section": "homemade", "biscuit": "a", "desc_source": "mom",
        "description": "Шоколадный бисквит на сметане и сгущённом молоке в сочетании со сливочно-шоколадным кремом."},
    "parizhskie-tayny": {"title": "Парижские тайны", "section": "homemade", "biscuit": "a", "desc_source": "mom",
        "description": "Белый бисквит на сметане и сгущённом молоке в сочетании со взбитыми сливками."},
    "rosinka": {"title": "Росинка", "section": "homemade", "biscuit": "a", "desc_source": "mom",
        "description": "Слои белого бисквита на сметане и сгущённом молоке с добавлением грецкого ореха прослоены сливочно-йогуртовым кремом."},
    "zemlenichnyy-desert": {"title": "Земляничный десерт", "section": "homemade", "biscuit": "a", "desc_source": "mom",
        "description": "Белый бисквит на сметане и сгущённом молоке в сочетании со взбитыми сливками с земляничным вкусом."},
    "shanhay": {"title": "Шанхай", "section": "homemade", "biscuit": "a", "desc_source": "mom",
        "description": "Слои шоколадного бисквита на сметане и сгущённом молоке в сочетании со взбитыми сливками с апельсиновым джемом.",
        "note": "Новое оформление, фото на следующей неделе."},
    "tiramisu": {"title": "Тирамису", "section": "homemade", "biscuit": "a", "desc_source": "mom",
        "description": "Слои белого бисквита на сметане и сгущённом молоке прослоены взбитыми сливками со вкусом кофе."},
    "praga": {"title": "Прага", "section": "homemade", "biscuit": "a", "desc_source": "pending",
        "description": "Бисквит на сметане и сгущённом молоке.",
        "note": "Ждём полное описание мамы (есть в другом письме)."},
    "sakura": {"title": "Сакура", "section": "homemade", "biscuit": "a", "desc_source": "pending",
        "description": "Бисквит на сметане и сгущённом молоке.",
        "note": "Ждём полное описание мамы."},
    "idilliya": {"title": "Идиллия", "section": "homemade", "biscuit": "a", "desc_source": "pending",
        "description": "Бисквит на сметане и сгущённом молоке.",
        "note": "Ждём полное описание мамы."},
    "chernosliv-v-shokolade": {"title": "Чернослив в шоколаде", "section": "homemade", "biscuit": "a", "desc_source": "pending",
        "description": "Бисквит на сметане и сгущённом молоке.",
        "note": "Ждём полное описание мамы."},
    "s-chersnoslivym": {"title": "С черносливом", "section": "homemade", "biscuit": "a", "desc_source": "pending",
        "description": "Бисквит на сметане и сгущённом молоке с черносливом.",
        "note": "Ждём полное описание мамы."},
    # ========== ДОМАШНИЕ — б) бисквит на сметане ==========
    "charodeyka": {"title": "Чародейка", "section": "homemade", "biscuit": "b", "desc_source": "mom",
        "description": "Слои белого бисквита на сметане прослоены сливочным кремом. Оформлен кокосовой стружкой и гелем.",
        "weights": [{"label": "0.6 кг", "price": "650 ₽"}, {"label": "1.0 кг", "price": "1 000 ₽"}]},
    "cheremukhovyy": {"title": "Черемуховый", "section": "homemade", "biscuit": "b", "desc_source": "mom",
        "description": "Белый бисквит на сметане с добавлением молотой черёмухи в сочетании со сливочным кремом."},
    "vishnevyy": {"title": "Вишневый", "section": "homemade", "biscuit": "b", "desc_source": "mom",
        "description": "Шоколадный бисквит на сметане с добавлением молотой вишни прослоен сливочным кремом с вишнёвым конфитюром.",
        "weights": [{"label": "0.6 кг", "price": "690 ₽"}, {"label": "1.1 кг", "price": "1 190 ₽"}]},
    # ========== ДОМАШНИЕ — в) бисквит на сгущённом молоке ==========
    "molochnaya-devochka": {"title": "Молочная девочка", "section": "homemade", "biscuit": "v", "desc_source": "mom",
        "description": "Слои белого бисквита на основе сгущённого молока прослоены взбитыми сливками с добавлением сливочно-сырного крема."},
    "tri-zhelaniya": {"title": "Три желания", "section": "homemade", "biscuit": "v", "desc_source": "mom",
        "description": "Три разных бисквита на основе сгущённого молока с добавлением какао, грецкого ореха и мака в сочетании со сливочно-йогуртовым кремом."},
    # ========== ДОМАШНИЕ — г) масляный бисквит ==========
    "shokoladnaya-devochka": {"title": "Шоколадная девочка", "section": "homemade", "biscuit": "g", "desc_source": "mom",
        "description": "Слои масляного бисквита с какао прослоены взбитыми сливками с добавлением сливочно-сырного крема.",
        "weights": [{"label": "0.65 кг", "price": "750 ₽"}]},
    "klubnichnoe-chudo": {"title": "Клубничное чудо", "section": "homemade", "biscuit": "g", "desc_source": "mom",
        "description": "Слои масляного бисквита в сочетании со взбитыми сливками с клубничным вкусом."},
    "eskimo": {"title": "Эскимо", "section": "homemade", "biscuit": "g", "desc_source": "mom",
        "description": "Слои масляного бисквита с ванильным суфле в сочетании со взбитыми сливками. Оформлен шоколадной глазурью."},
    "izobilie": {"title": "Изобилие", "section": "homemade", "biscuit": "g", "desc_source": "mom",
        "description": "Масляный бисквит со сгущённым молоком с добавлением грецкого ореха прослоен сливочным кремом с кусочками чернослива."},

    # ========== НОВЫЕ ТОРТЫ (фото из new cakes2, письма 30.06–01.07) ==========
    "krasnyy-barhat": {"title": "Красный бархат", "section": "other", "desc_source": "pending",
        "description": "Бисквит «Красный бархат» со сливочно-сырным кремом.",
        "note": "Ждём описание и вес от мамы."},
    "slavutich": {"title": "Славутич", "section": "other", "desc_source": "pending",
        "description": "Медово-шоколадные коржи со сливочным кремом.",
        "weights": [{"label": "1,5 кг", "price": "уточняйте"}],
        "note": "Ждём описание от мамы."},
    "elbrus": {"title": "Эльбрус", "section": "other", "desc_source": "pending",
        "description": "Бисквитный торт со сливочным кремом и воздушным безе.",
        "weights": [{"label": "0,9 кг", "price": "уточняйте"}],
        "note": "Ждём описание от мамы."},
    "fistashkovyy": {"title": "Фисташковый", "section": "other", "desc_source": "pending",
        "description": "Фисташковый бисквит со сливочным кремом.",
        "weights": [{"label": "0,8 кг", "price": "уточняйте"}],
        "note": "Ждём описание от мамы."},
    "tsarskiy-bananovyy": {"title": "Царский (банановый)", "section": "other", "desc_source": "pending",
        "description": "Царский торт с банановой начинкой.",
        "note": "Ждём описание и вес от мамы."},
    "polet-premium": {"title": "Полёт-Премиум", "section": "other", "desc_source": "pending",
        "description": "Воздушно-ореховое безе со сливочным кремом.",
        "weights": [{"label": "1,0 кг", "price": "уточняйте"}],
        "note": "Ждём полное описание от мамы."},
    "polet-kedrovyy": {"title": "Полёт с кедровым орехом", "section": "other", "desc_source": "pending",
        "description": "Воздушно-ореховое безе с кедровым орехом и сливочным кремом.",
        "weights": [{"label": "0,5 кг", "price": "уточняйте"}],
        "note": "Ждём полное описание от мамы."},
    "polet-varenka": {"title": "Полёт с варёным сгущённым молоком", "section": "other", "desc_source": "pending",
        "description": "Воздушно-ореховое безе со сливочным кремом на варёном сгущённом молоке.",
        "weights": [{"label": "0,5 кг", "price": "уточняйте"}, {"label": "1,0 кг", "price": "уточняйте"}],
        "note": "Ждём полное описание от мамы."},
    "polet-slivochnyy": {"title": "Полёт со сливочным кремом", "section": "other", "desc_source": "pending",
        "description": "Воздушно-ореховое безе со сливочным кремом.",
        "weights": [{"label": "0,5 кг", "price": "уточняйте"}, {"label": "1,0 кг", "price": "уточняйте"}],
        "note": "Ждём полное описание от мамы."},

    # ========== ПИРОЖНОЕ (фото из new cakes2) ==========
    "grafskie-razvaliny": {"title": "Графские развалины", "section": "pastries", "desc_source": "mom",
        "description": "Крошка воздушного безе с орехом в сочетании со сливочным кремом с варёной сгущёнкой.",
        "weights": [{"label": "0,8 кг", "price": "840 ₽"}]},
    "korzinochka": {"title": "Корзиночка", "section": "pastries", "desc_source": "mom",
        "description": "Корзиночка из песочного теста, наполнена яблочным повидлом, украшена белковым кремом, консервированной вишней или желейной ягодой.",
        "weights": [{"label": "160 гр", "price": "265 ₽"}]},
    "eklery": {"title": "Эклеры", "section": "pastries", "desc_source": "mom",
        "description": "Заварное тесто с варёной сгущёнкой или белково-сливочным кремом.",
        "weights": [{"label": "50 гр", "price": "80-90 ₽"}]},
    "kolco-zavarnoe": {"title": "Кольцо заварное", "section": "pastries", "desc_source": "pending",
        "description": "Заварное кольцо.",
        "weights": [{"label": "30 гр", "price": "55 ₽"}],
        "note": "Ждём описание от мамы."},
    "biskvitno-kremovoe": {"title": "Бисквитно-кремовое", "section": "pastries", "desc_source": "pending",
        "description": "Бисквитно-кремовое пирожное.",
        "weights": [{"label": "0,375 кг", "price": "445 ₽"}],
        "note": "Ждём описание от мамы."},
    "biskvitno-kremovoe-sufle": {"title": "Бисквитно-кремовое с суфле", "section": "pastries", "desc_source": "pending",
        "description": "Бисквитно-кремовое пирожное с суфле.",
        "weights": [{"label": "0,450 кг", "price": "600 ₽"}],
        "note": "Ждём описание от мамы."},

    # ========== ДРУГИЕ (есть фото, мама пока не классифицировала/не описала) ==========
    "vishnya-so-slivkami": {"title": "Вишня со сливками", "section": "other", "desc_source": "placeholder",
        "description": "Нежный бисквит с вишнёвой начинкой и воздушными сливками."},
    "kurskiy": {"title": "Курский", "section": "other", "desc_source": "placeholder",
        "description": "Песочные коржи с нежной начинкой по традиционному рецепту."},
    "elitnyy": {"title": "Элитный", "section": "other", "desc_source": "placeholder",
        "description": "Бисквитный торт премиального уровня с изысканным кремом и декором."},
    "chernyy-lyuks": {"title": "Чёрный Люкс", "section": "other", "desc_source": "placeholder",
        "description": "Изысканный шоколадный торт премиум-класса с насыщенным вкусом и благородным оформлением.",
        "weights": [{"label": "1.3 кг", "price": "1 950 ₽"}]},
    "snikers": {"title": "Сникерс", "section": "other", "desc_source": "placeholder",
        "description": "Шоколадный торт с карамелью, арахисом и нежным кремом."},
    "tryufelnyy": {"title": "Трюфельный", "section": "other", "desc_source": "placeholder",
        "description": "Насыщенный шоколадный вкус с трюфельной начинкой и бархатистым кремом."},
    "prazdnichnyy": {"title": "Праздничный", "section": "other", "desc_source": "placeholder",
        "description": "Яркий праздничный торт с праздничным декором для особых случаев."},
    "fantaziya": {"title": "Фантазия", "section": "other", "desc_source": "placeholder",
        "description": "Праздничный торт с авторским декором и нежным кремом."},
    "soblazn": {"title": "Соблазн", "section": "other", "desc_source": "placeholder",
        "description": "Изысканный фирменный торт с насыщенным вкусом и элегантным оформлением."},
    "tsarskiy": {"title": "Царский", "section": "other", "desc_source": "placeholder",
        "description": "Премиальный торт с богатым декором и насыщенным вкусом."},
    "lakomka": {"title": "Лакомка", "section": "other", "desc_source": "pending",
        "description": "Шоколадно-ореховый торт со сгущённым молоком.",
        "weights": [{"label": "1,0 кг", "price": "уточняйте"}],
        "note": "Ждём описание от мамы."},
}

DEFAULT_WEIGHTS = [{"label": "1 кг", "price": "уточняйте"}]

# Пирожные теперь входят в CAKE_META (section="pastries"), печенья без фото — не показываем.
# Пустые списки оставлены для совместимости импортов (status_report.py).
PASTRIES: list[dict] = []
COOKIES: list[dict] = []


def parse_new_cake_name_fixed(filename: str) -> tuple[str, str] | None:
    """Extended parser for typos and space-separated names."""
    stem = Path(filename).stem.lower().replace("ё", "е")
    stem = stem.replace("рразрез", "разрез").replace("разрезjpg", "разрез")

    if " разрез" in stem:
        name = stem.split(" разрез")[0].strip("- ")
        return slugify(name), "cut"

    parsed = parse_new_cake_name(filename)
    if parsed:
        return parsed

    if stem.endswith("разрез"):
        name = stem[: -len("разрез")].strip("- ")
        if name:
            return slugify(name), "cut"
    if stem.endswith("общий"):
        name = stem[: -len("общий")].strip("- ")
        if name:
            return slugify(name), "whole"
    return None


def collect_image_jobs() -> tuple[list[tuple], dict, list[str]]:
    catalog_images: dict = {}
    unmapped: list[str] = []
    slot_taken: set[tuple[str, str]] = set()
    jobs: list[tuple[Path, Path, str, str, str]] = []

    def add_job(src: Path, dst: Path, slug: str, view: str, kind: str, force: bool = False) -> None:
        key = (slug, view)
        if slug.startswith("_"):
            jobs.append((src, dst, slug, view, kind))
            return
        if key in slot_taken and not force:
            if kind == "old":
                return
        if kind == "new":
            slot_taken.discard(key)
        slot_taken.add(key)
        jobs.append((src, dst, slug, view, kind))

    if NEW_CAKES.exists():
        for src in sorted(NEW_CAKES.iterdir()):
            if src.suffix.lower() not in IMAGE_EXTS:
                continue
            parsed = parse_new_cake_name_fixed(src.name)
            if not parsed:
                unmapped.append(str(src.relative_to(ROOT)))
                continue
            slug, view = parsed
            dst = WEBP_ROOT / "cakes" / f"{slug}-{view}.webp"
            add_job(src, dst, slug, view, "new")

    if NEW_CAKES2.exists():
        for src in sorted(NEW_CAKES2.iterdir()):
            if src.suffix.lower() not in IMAGE_EXTS:
                continue
            mapping = NEW_CAKES2_MAP.get(src.name) or parse_new_cake_name_fixed(src.name)
            if not mapping:
                unmapped.append(str(src.relative_to(ROOT)))
                continue
            slug, view = mapping
            dst = WEBP_ROOT / "cakes" / f"{slug}-{view}.webp"
            add_job(src, dst, slug, view, "new")

    if OLD_CAKES.exists():
        for src in sorted(OLD_CAKES.iterdir()):
            if src.suffix.lower() not in IMAGE_EXTS:
                continue
            stem = src.stem
            if stem not in OLD_FILE_MAP:
                unmapped.append(str(src.relative_to(ROOT)))
                continue
            slug, view = OLD_FILE_MAP[stem]
            if slug == "tort-s-chernoslivom":
                slug = "s-chersnoslivym"
            if slug == "zemlyanichnyy-desert":
                slug = "zemlenichnyy-desert"
            if slug.startswith("_"):
                sub = "misc" if slug == "_promo" else "backgrounds"
                dst = WEBP_ROOT / sub / f"{slugify(stem)}.webp"
            else:
                dst = WEBP_ROOT / "cakes" / f"{slug}-{view}.webp"
            add_job(src, dst, slug, view, "old")

    hero = ASSETS / "hero.png"
    if hero.exists():
        jobs.append((hero, WEBP_ROOT / "hero.webp", "hero", "whole", "hero"))

    berries = ASSETS / "berries"
    if berries.exists():
        for src in sorted(berries.iterdir()):
            if src.suffix.lower() not in IMAGE_EXTS:
                continue
            dst = WEBP_ROOT / "berries" / f"{slugify(src.stem)}.webp"
            jobs.append((src, dst, src.stem, "whole", "berry"))

    return jobs, catalog_images, unmapped


def run_conversion(jobs: list) -> dict:
    catalog: dict = {"cakes": {}, "other": []}
    print(f"Converting {len(jobs)} images to WebP...")
    for i, (src, dst, slug, view, kind) in enumerate(jobs, 1):
        print(f"[{i}/{len(jobs)}] {src.name} -> {dst.relative_to(ROOT)}")
        try:
            ffmpeg_to_webp(src, dst)
        except subprocess.CalledProcessError as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            continue

        if kind in {"new", "old"} and not slug.startswith("_"):
            cake = catalog["cakes"].setdefault(slug, {"slug": slug, "images": {}, "sources": []})
            cake["images"][view] = rel_webp(dst)
            cake["sources"].append({"file": str(src.relative_to(ROOT)), "view": view, "origin": kind})
        else:
            catalog["other"].append({"slug": slug, "webp": rel_webp(dst), "source": str(src.relative_to(ROOT))})
    return catalog


_PRICE_TABLE = price_parse()


def resolve_weights(meta: dict) -> tuple[list[dict], str]:
    """Реальные цены из прайса -> иначе ручные -> иначе заглушка."""
    from_price = price_weights_for_title(meta["title"], _PRICE_TABLE)
    if from_price:
        return from_price, "price-list"
    if meta.get("weights"):
        return meta["weights"], "manual"
    return DEFAULT_WEIGHTS, "none"


def product_item(slug: str, meta: dict, catalog: dict) -> dict:
    imgs = catalog["cakes"].get(slug, {}).get("images", {})
    weights, _ = resolve_weights(meta)
    item = {
        "title": meta["title"],
        "slug": slug,
        "description": meta["description"],
        "weights": weights,
        "hasWhole": "whole" in imgs,
        "hasCut": "cut" in imgs,
    }
    if meta.get("note"):
        item["note"] = meta["note"]
    return item


def ordered_slugs() -> list[str]:
    return list(CAKE_META.keys())


def build_products(catalog: dict) -> dict:
    products: dict[str, list] = {s["id"]: [] for s in SECTIONS}

    homemade: list[str] = []
    for slug, meta in CAKE_META.items():
        section = meta["section"]
        if section == "homemade":
            homemade.append(slug)
        else:
            products[section].append(product_item(slug, meta, catalog))

    homemade.sort(key=lambda s: BISCUIT_ORDER.get(CAKE_META[s].get("biscuit"), 9))
    for slug in homemade:
        products["homemade"].append(product_item(slug, CAKE_META[slug], catalog))

    return products


def write_products_js(products: dict) -> None:
    # На сайт — только позиции с фотографией (есть общий вид или разрез).
    # Без разреза — это нормально, главное чтобы была хотя бы одна картинка.
    filtered: dict[str, list] = {}
    for sid, items in products.items():
        kept = [it for it in items if it.get("hasWhole") or it.get("hasCut")]
        filtered[sid] = kept

    sections = [s for s in SECTIONS if filtered.get(s["id"])]
    payload = {"sections": sections, "products": filtered}
    out = ROOT / "src" / "products-data.js"
    out.write_text(
        "/* eslint-disable */\n"
        "// Auto-generated by scripts/build_catalog.py — do not edit by hand.\n"
        f"window.PRODUCTS_DATA = {json.dumps(payload, ensure_ascii=False, indent=2)};\n",
        encoding="utf-8",
    )
    print(f"Products JS: {out}")


def write_catalog_json(catalog: dict, products: dict, unmapped: list[str]) -> None:
    for slug, meta in CAKE_META.items():
        if slug in catalog["cakes"]:
            catalog["cakes"][slug].update({
                "title": meta["title"],
                "section": meta["section"],
                "biscuit": meta.get("biscuit"),
                "description": meta["description"],
                "desc_source": meta["desc_source"],
            })

    out = {
        "generated_by": "scripts/build_catalog.py",
        "sections": SECTIONS,
        "cakes": catalog["cakes"],
        "products": products,
        "unmapped_sources": unmapped,
    }
    path = ROOT / "data" / "product-images-catalog.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Catalog JSON: {path}")


def write_product_doc(products: dict, catalog: dict) -> None:
    """Единый док продуктовой линейки для нейросети / контроля."""
    cakes_img = catalog.get("cakes", {})

    def photo(slug: str) -> str:
        imgs = cakes_img.get(slug, {}).get("images", {})
        v = []
        if "whole" in imgs:
            v.append("общий")
        if "cut" in imgs:
            v.append("разрез")
        return " + ".join(v) if v else "нет фото"

    lines = [
        "# Продуктовая линейка — фабрика «Восток» (Чита)",
        "",
        "Автогенерация: `python scripts/build_catalog.py`. Структура и описания — по письмам заказчицы.",
        "Источник описания: **мамино** / *заглушка* / *ждёт описания*.",
        "",
        "## Разделы",
        "",
    ]
    for s in SECTIONS:
        lines.append(f"- **{s['label']}** — {len(products.get(s['id'], []))} позиций")
    lines.append("")

    src_label = {"mom": "мамино", "placeholder": "заглушка", "pending": "ждёт описания"}

    for s in SECTIONS:
        sid = s["id"]
        items = products.get(sid, [])
        if not items:
            continue
        lines.append(f"## {s['label']} ({len(items)})")
        lines.append("")
        last_biscuit = object()
        for it in items:
            slug = it.get("slug")
            meta = CAKE_META.get(slug, {}) if slug else {}
            if sid == "homemade":
                biscuit = meta.get("biscuit")
                if biscuit != last_biscuit:
                    last_biscuit = biscuit
                    lines.append(f"**— {BISCUIT_LABEL.get(biscuit, 'прочее')} —**")
                    lines.append("")
            src = src_label.get(meta.get("desc_source"), "—")
            ph = photo(slug) if slug else "—"
            lines.append(f"### {it['title']} (`{slug or '—'}`)")
            lines.append(f"- Описание ({src}): {it['description']}")
            lines.append(f"- Фото: {ph}")
            if it.get("note"):
                lines.append(f"- ⚠ {it['note']}")
            lines.append("")

    path = ROOT / "data" / "PRODUCT-LINE.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Doc: {path}")


def main() -> int:
    skip_images = "--skip-images" in sys.argv
    jobs, _, unmapped = collect_image_jobs()
    if skip_images:
        catalog_path = ROOT / "data" / "product-images-catalog.json"
        if catalog_path.exists():
            saved = json.loads(catalog_path.read_text(encoding="utf-8"))
            catalog = {"cakes": saved.get("cakes", {}), "other": saved.get("other", [])}
            print("Skipping image conversion, using existing catalog.")
        else:
            print("No catalog found, running conversion...")
            catalog = run_conversion(jobs)
    else:
        catalog = run_conversion(jobs)

    products = build_products(catalog)
    write_products_js(products)
    write_catalog_json(catalog, products, unmapped)
    write_product_doc(products, catalog)

    total = sum(len(products[s["id"]]) for s in SECTIONS)
    cakes_total = sum(len(products[s["id"]]) for s in SECTIONS if s["id"] not in ("pastries", "cookies"))
    print(f"\nDone. Всего позиций: {total}; тортов: {cakes_total}; с фото: {len(catalog['cakes'])}")
    print(f"Unmapped files: {len(unmapped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
