# Зелёная полка

Веб‑магазин с доставкой овощей, фруктов и зелени: каталог, корзина, оформление с проверкой адреса на карте, трекинг заказа и роли для персонала.

**Стек:** Python 3, Flask, Jinja2, SQLite, Leaflet (карта), vanilla JS.

## Возможности

- Каталог с локальными фото товаров, корзина без перезагрузки страницы
- Оформление заказа: интерактивная карта, зона доставки, сохранённые адреса
- Публичный код заказа `ZP-******` и страница статуса
- Роли: покупатель, сборщик, курьер, администратор
- Админка: диспетчер заказов, каталог, остатки, стоп‑лист

## Быстрый старт (Windows)

```powershell
cd kursach
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Откройте [http://127.0.0.1:5000](http://127.0.0.1:5000).

При первом запуске создаётся `zelenaya_polka.db` и заполняется демо‑каталогом.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Демо‑аккаунты

| Логин  | Пароль | Роль        |
|--------|--------|-------------|
| user1  | user1  | Покупатель  |
| user2  | user2  | Сборщик     |
| user3  | user3  | Курьер      |
| admin  | admin  | Администратор |

## Основные маршруты

| URL | Описание |
|-----|----------|
| `/` | Главная |
| `/catalog` | Каталог |
| `/cart`, `/checkout` | Корзина и оформление |
| `/delivery` | Зона доставки на карте |
| `/orders/track` | Поиск заказа по коду |
| `/auth/login` | Вход |
| `/admin/` | Панель администратора |
| `/picker/` | Заказы на сборку |
| `/courier/` | Доставки курьера |

## Карта и зона доставки

Конур зоны и координаты магазинов подгружаются из виджета [конструктора 2ГИС](https://platform.2gis.ru/map-constructor).

- Переменная `DGIS_MAP_WIDGET_URL` в `config.py` (или в окружении)
- Кэш: `app/static/data/delivery-map.json`
- На сервере адрес проверяется функцией `point_in_delivery_zone` (`app/geo.py`)

После смены контура в 2ГИС перезапустите приложение.

## Конфигурация (переменные окружения)

| Переменная | Назначение |
|------------|------------|
| `SECRET_KEY` | Ключ сессии Flask (обязательно сменить на проде) |
| `DATABASE_URL` | URI БД (по умолчанию SQLite в корне проекта) |
| `DGIS_MAP_WIDGET_URL` | URL виджета 2ГИС с полигоном зоны |
| `SITE_PUBLIC_URL` | Публичный базовый URL (для абсолютных ссылок при деплое) |

## Структура проекта

```
app/
  blueprints/   # shop, orders, auth, admin, picker, courier, account
  templates/    # Jinja2
  static/       # CSS, JS, изображения, delivery-map.json
  models.py     # SQLAlchemy-модели
  stock.py      # остатки и валидация корзины
  geo.py        # проверка точки в зоне
config.py
run.py
requirements.txt
```

## Дизайн

| Цвет | HEX |
|------|-----|
| Sage | `#8B9A6E` |
| Cream | `#F7F2EB` |
| Beige | `#EAE2D6` |
| Grey | `#EEEEEE` |

## Деплой

Минимально: WSGI‑сервер (gunicorn/waitress) + `SECRET_KEY` + постоянный том для SQLite или внешняя БД через `DATABASE_URL`.

```bash
pip install -r requirements.txt
# пример
waitress-serve --listen=0.0.0.0:8000 run:app
```

---

Учебный / pet‑project. Пул‑реквесты и issues приветствуются.