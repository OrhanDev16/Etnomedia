# Этномедиа — REST API онлайн-кинотеатра

Backend онлайн-кинотеатра этнического кино на **Django REST Framework**.
Каталог фильмов, сериалов, мультфильмов и документального кино народов Центральной Азии: фильтры по жанру, народу, стране и языку, сезоны и серии, избранное, история просмотра, оценки, отзывы с модерацией и платная подписка на премиум-контент.

## Стек

- **Python 3.12+**, **Django 6.1**, **Django REST Framework**
- **Simple JWT** — вход по email, access / refresh токены
- **django-filter** — фильтрация, поиск и сортировка
- **drf-spectacular** — Swagger-документация API
- **django-cors-headers** — подключение frontend (Vite, порт 5173)
- Pillow, SQLite

## Возможности

- Регистрация с подтверждением пароля, вход по **email**, профиль и смена пароля
- Каталог: фильмы, сериалы, мультфильмы, документальные; возрастной рейтинг 0+…18+
- Фильтры по типу, жанру, стране, народу, языку, году (от / до), возрасту и премиуму
- Поиск по названию, описанию и актёрам, подсказки в строке поиска
- Сортировка по дате, рейтингу, просмотрам, названию и году; пагинация по 20
- Карточка фильма: съёмочная группа с ролями, средний рейтинг и число голосов, похожие фильмы
- Сериалы: сезоны и серии
- Просмотр: ссылка на видео выдаётся через `/stream/`, премиум-контент только с активной подпиской
- «Продолжить просмотр»: сохраняется позиция; при 95 % фильм считается досмотренным
- Избранное (без дублей), оценки 1–10, отзывы проходят модерацию в админке
- Тарифы и подписки: новая подписка начинается после окончания текущей
- Админ-панель на русском
- Скрипт `seed.py` наполняет базу демо-данными: 20 фильмов и сериалов с постерами

## Модели

| Группа | Модели |
|---|---|
| Пользователи | `User` (вход по email) |
| Справочники | `Genre`, `Country`, `Ethnos`, `Language`, `Person` |
| Каталог | `Content`, `ContentPerson`, `Season`, `Episode` |
| Просмотр | `Favorite`, `WatchProgress`, `Rating`, `Review` |
| Подписки | `Plan`, `Subscription` |

## API

Базовый адрес: `http://127.0.0.1:8000/api/v1/`
🔒 — нужен заголовок `Authorization: Bearer <access_token>`.

**Пользователи**

| Метод | URL | Описание |
|---|---|---|
| POST | `auth/register/` | регистрация (`email`, `username`, `password`, `password2`) |
| POST | `auth/token/` | вход по `email` и `password` → `access` и `refresh` |
| POST | `auth/token/refresh/` | новый access-токен |
| GET, PATCH | `users/me/` | мой профиль 🔒 |
| POST | `users/me/change-password/` | смена пароля 🔒 |

**Каталог**

| Метод | URL | Описание |
|---|---|---|
| GET | `content/` | список с фильтрами, поиском и сортировкой |
| GET | `content/featured/` | баннер на главной |
| GET | `content/<slug>/` | карточка фильма |
| GET | `content/<slug>/similar/` | похожие фильмы |
| GET | `content/<slug>/seasons/` | сезоны и серии |
| GET | `content/<slug>/stream/` | ссылка на видео (премиум — с подпиской) |
| GET | `episodes/<id>/stream/` | ссылка на видео серии |
| PUT | `content/<slug>/rating/` | поставить оценку 1–10 🔒 |
| GET, POST | `content/<slug>/reviews/` | отзывы, оставить отзыв 🔒 |
| DELETE | `reviews/<id>/` | удалить свой отзыв 🔒 |
| GET | `search/suggest/?q=...` | подсказки поиска |
| GET | `genres/`, `countries/`, `ethnoses/`, `languages/` | справочники для фильтров |
| GET | `persons/`, `persons/<id>/` | актёры и режиссёры с фильмографией |

**Просмотр и подписки**

| Метод | URL | Описание |
|---|---|---|
| GET, POST | `favorites/` | избранное, добавить (`content_id`) 🔒 |
| DELETE | `favorites/<content_id>/` | убрать из избранного 🔒 |
| POST | `progress/` | сохранить позицию просмотра 🔒 |
| GET | `history/` | история просмотров 🔒 |
| GET | `history/continue/` | «Продолжить просмотр» 🔒 |
| GET | `plans/` | тарифы |
| POST | `subscriptions/` | оформить подписку (`plan_id`) 🔒 |
| GET | `subscriptions/me/` | моя активная подписка 🔒 |

Параметры для `content/`:

```
?type=series           film, series, cartoon, documentary
?genre=genre-0         по slug жанра
?ethnos=ethnos-0       по slug народа
?country=country-0     по slug страны
?language=ky           по коду языка: ky, ru, kk, uz
?year_min=2020&year_max=2024
?age=12%2B             возрастной рейтинг 12+ (знак + в адресе пишется как %2B)
?premium=true          только премиум
?search=Манас          поиск
?ordering=-rating      created_at, rating, views_count, title, year
```

Полная документация — в Swagger: `/api/docs/`

## Запуск проекта

```bash
git clone https://github.com/OrhanDev16/Etnomedia.git
cd Etnomedia
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
python manage.py migrate
python seed.py
python manage.py createsuperuser
python manage.py runserver
```

`seed.py` заполняет базу демо-фильмами. Чтобы заполнить заново с нуля: `python seed.py --clear`.
`createsuperuser` спрашивает email, а не логин.

| Что | Адрес |
|---|---|
| API | http://127.0.0.1:8000/api/v1/ |
| Swagger | http://127.0.0.1:8000/api/docs/ |
| Админка | http://127.0.0.1:8000/admin/ |

## Структура проекта

```
Etnomedia/
├── my_site/          # настройки и главные URL
├── store_app/
│   ├── models.py
│   ├── views.py      # сериализаторы, фильтры и views
│   ├── urls.py
│   └── admin.py
├── seed.py           # демо-данные
├── manage.py
└── requirements.txt
```

## Автор

**OrhanDev16** — [github.com/OrhanDev16](https://github.com/OrhanDev16)