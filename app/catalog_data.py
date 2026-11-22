"""Catalog categories and product definitions (single source of truth)."""

CATALOG_CATEGORIES = (
    {"id": "овощи", "label": "Овощи"},
    {"id": "фрукты", "label": "Фрукты"},
    {"id": "зелень", "label": "Зелень"},
    {"id": "ягоды", "label": "Ягоды"},
)

CATEGORY_IDS = tuple(c["id"] for c in CATALOG_CATEGORIES)
CATEGORY_SORT_INDEX = {c["id"]: i for i, c in enumerate(CATALOG_CATEGORIES)}

# name, description, price, unit, category, emoji, image path under static
PRODUCTS = [
    # —— овощи ——
    ("Томаты круглые", "Спелые, для салатов и соусов", 210, "кг", "овощи", "🍅", "img/products/tomaty-kruglye.jpg"),
    ("Огурцы тепличные", "Хрустящие, идеальны для салата", 180, "кг", "овощи", "🥒", "img/products/ogurcy-teplichnye.jpg"),
    ("Морковь молодая", "С кисточкой зелени", 95, "кг", "овощи", "🥕", "img/products/morkov.jpg"),
    ("Картофель молодой", "Нежная кожура, быстрая готовка", 110, "кг", "овощи", "🥔", "img/products/kartofel.jpg"),
    ("Лук репчатый", "Классика для супов и жарки", 55, "кг", "овощи", "🧅", "img/products/luk-repchatyy.jpg"),
    ("Кабачки", "Нежные, для тушения и гриля", 130, "кг", "овощи", "🥒", "img/products/kabachki.jpg"),
    ("Свёкла", "Сладкая, яркая", 75, "кг", "овощи", "🟣", "img/products/svekla.jpg"),
    ("Брокколи", "Свежесрезанная капуста", 280, "кг", "овощи", "🥦", "img/products/brokkoli.jpg"),
    ("Перец болгарский", "Микс красный и жёлтый", 350, "кг", "овощи", "🫑", "img/products/perets.jpg"),
    ("Чеснок", "Ароматный, плотные головки", 320, "кг", "овощи", "🧄", "img/products/chesnok.jpg"),
    # —— фрукты ——
    ("Яблоки Гала", "Сладкие, хрустящие", 160, "кг", "фрукты", "🍎", "img/products/yabloki-gala.jpg"),
    ("Яблоки Голден", "Медовый вкус, сочные", 150, "кг", "фрукты", "🍎", "img/products/yabloki-golden.jpg"),
    ("Груши Конференция", "Сладкие, тают во рту", 210, "кг", "фрукты", "🍐", "img/products/grushi.jpg"),
    ("Бананы", "Спелые, без чёрных пятен", 120, "кг", "фрукты", "🍌", "img/products/banany.jpg"),
    ("Апельсины", "Сочные, для сока и перекуса", 140, "кг", "фрукты", "🍊", "img/products/apelsiny.jpg"),
    ("Мандарины", "Легко чистятся, сладкие", 170, "кг", "фрукты", "🍊", "img/products/mandariny.jpg"),
    ("Виноград", "Сочные грозди", 290, "кг", "фрукты", "🍇", "img/products/vinograd.jpg"),
    ("Грейпфрут", "Лёгкая горчинка, бодрит", 130, "шт", "фрукты", "🍊", "img/products/greypfrut.jpg"),
    ("Авокадо Хасс", "Мягкие, для тостов и салатов", 190, "шт", "фрукты", "🥑", "img/products/avokado.jpg"),
    ("Лимоны", "Ароматные", 220, "кг", "фрукты", "🍋", "img/products/limony.jpg"),
    # —— зелень ——
    ("Зелёный лук", "Пучок", 60, "пучок", "зелень", "🧅", "img/products/luk-zelenyy.jpg"),
    ("Укроп", "Ароматный пучок", 45, "пучок", "зелень", "🌿", "img/products/ukrop.jpg"),
    ("Петрушка", "Свежая", 45, "пучок", "зелень", "🌿", "img/products/petrushka.jpg"),
    ("Кинза", "Яркий аромат", 50, "пучок", "зелень", "🌿", "img/products/kinza.jpg"),
    ("Шпинат", "Молодой лист", 90, "г", "зелень", "🥬", "img/products/shpinat.jpg"),
    ("Салат ромэн", "Хрустящий лист", 120, "шт", "зелень", "🥬", "img/products/salat-romen.jpg"),
    ("Руккола", "Пряная, для салатов", 85, "г", "зелень", "🥗", "img/products/rukkola.jpg"),
]

PRODUCT_IMAGES = {name: image for name, *_, image in PRODUCTS}
