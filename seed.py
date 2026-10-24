# Заполнение базы демо-данными.
# Запуск: python seed.py  (из папки, где лежит manage.py)
# Заполнить заново с нуля: python seed.py --clear

import io
import os
import random
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_site.settings')
django.setup()

from django.core.files.base import ContentFile  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from store_app.models import (  # noqa: E402
    Genre, Country, Ethnos, Language, Person, Content, ContentPerson, Season, Episode, Plan,
)

# цвета постеров: (верх, низ)
COLORS = [
    ((176, 42, 42), (58, 10, 18)),
    ((30, 90, 160), (8, 26, 64)),
    ((38, 122, 64), (8, 40, 22)),
    ((184, 112, 30), (70, 30, 8)),
    ((96, 52, 156), (30, 10, 62)),
    ((20, 120, 130), (6, 40, 46)),
]

GENRES = ['Драма', 'Комедия', 'Исторический', 'Документальный', 'Мелодрама', 'Семейный', 'Мультфильм']
ETHNOSES = ['Кыргызы', 'Казахи', 'Узбеки', 'Таджики', 'Якуты']
COUNTRIES = ['Кыргызстан', 'Казахстан', 'Узбекистан', 'Россия']
LANGUAGES = [('Кыргызский', 'ky'), ('Русский', 'ru'), ('Казахский', 'kk'), ('Узбекский', 'uz')]
PERSONS = ['Айбек Осмонов', 'Нурлан Абдыкадыров', 'Айсулуу Токтосунова', 'Бакыт Мамбетов',
           'Динара Асанова', 'Эрлан Жумабаев', 'Гульнара Сейитбекова', 'Талант Кадыров']

# название, год, жанр, народ, страна, язык, тип, премиум, на главной
FILMS = [
    ('Окул ата', 2022, 'Драма', 'Кыргызы', 'Кыргызстан', 'ky', 'film', False, True),
    ('Күйөө жолдош', 2022, 'Комедия', 'Кыргызы', 'Кыргызстан', 'ky', 'film', False, True),
    ('Новая сила', 2022, 'Драма', 'Кыргызы', 'Кыргызстан', 'ru', 'film', False, True),
    ('Кайнене 2', 2022, 'Комедия', 'Кыргызы', 'Кыргызстан', 'ky', 'film', True, False),
    ('Чайки-Зайки 2', 2022, 'Комедия', 'Кыргызы', 'Кыргызстан', 'ky', 'film', False, False),
    ('10 жылдык', 2022, 'Драма', 'Кыргызы', 'Кыргызстан', 'ky', 'film', False, False),
    ('Ак жол', 2026, 'Семейный', 'Кыргызы', 'Кыргызстан', 'ky', 'film', True, True),
    ('Тоо арасында', 2025, 'Мелодрама', 'Кыргызы', 'Кыргызстан', 'ky', 'film', False, False),
    ('Дала әні', 2025, 'Драма', 'Казахи', 'Казахстан', 'kk', 'film', False, False),
    ('Кербен', 2024, 'Исторический', 'Узбеки', 'Узбекистан', 'uz', 'film', True, False),
    ('Ата-журт', 2024, 'Исторический', 'Кыргызы', 'Кыргызстан', 'ky', 'film', False, False),
    ('Жайлоо', 2024, 'Документальный', 'Кыргызы', 'Кыргызстан', 'ky', 'documentary', False, False),
    ('Памир', 2023, 'Документальный', 'Таджики', 'Россия', 'ru', 'documentary', False, False),
    ('Олонхо', 2023, 'Драма', 'Якуты', 'Россия', 'ru', 'film', True, False),
    ('Апам экөөбүз', 2023, 'Мелодрама', 'Кыргызы', 'Кыргызстан', 'ky', 'film', False, False),
    ('Аламан', 2023, 'Комедия', 'Казахи', 'Казахстан', 'kk', 'film', False, False),
    ('Кичинекей Манас', 2025, 'Мультфильм', 'Кыргызы', 'Кыргызстан', 'ky', 'cartoon', False, False),
    ('Тулпар', 2024, 'Мультфильм', 'Кыргызы', 'Кыргызстан', 'ky', 'cartoon', False, False),
]

# сериалы: название, год, жанр, народ, сколько сезонов, серий в сезоне
SERIES = [
    ('Айыл турмушу', 2025, 'Комедия', 'Кыргызы', 2, 6),
    ('Шаар жарыгы', 2026, 'Драма', 'Кыргызы', 1, 8),
]

DESCRIPTIONS = {
    'Драма': 'Жизненная история о семье, выборе и ответственности перед близкими.',
    'Комедия': 'Лёгкая семейная комедия с узнаваемыми героями и бытовыми ситуациями.',
    'Исторический': 'Фильм о событиях прошлого и людях, которые сохранили память народа.',
    'Документальный': 'Документальный рассказ о природе, традициях и жизни людей.',
    'Мелодрама': 'Трогательная история любви на фоне гор и родного аила.',
    'Семейный': 'Тёплое кино для всей семьи.',
    'Мультфильм': 'Анимационная история для детей по мотивам народных сказаний.',
}


def make_image(text, width, height, colors):
    # рисуем постер: градиент + название
    top, bottom = colors
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        t = y / height
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)

    def load_font(size):
        for name in ['arialbd.ttf', 'DejaVuSans-Bold.ttf']:  # Windows, Linux
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                pass
        return ImageFont.load_default()

    # название в одну строку; если не влезает — в две
    words = text.upper().split()
    lines = [text.upper()]
    size = width // 9 if width < 800 else width // 16
    font = load_font(size)
    if draw.textlength(lines[0], font=font) > width * 0.9 and len(words) > 1:
        half = (len(words) + 1) // 2
        lines = [' '.join(words[:half]), ' '.join(words[half:])]

    # уменьшаем шрифт, пока самая длинная строка не влезет
    while size > 12 and max(draw.textlength(line, font=font) for line in lines) > width * 0.9:
        size -= 2
        font = load_font(size)

    y = int(height * 0.72)
    for line in lines:
        draw.text((width // 2, y), line, font=font, fill=(255, 214, 70), anchor='mm')
        y += int(size * 1.2)

    buffer = io.BytesIO()
    image.save(buffer, 'JPEG', quality=85)
    return ContentFile(buffer.getvalue())


def add_media(content, index):
    colors = COLORS[index % len(COLORS)]
    content.poster.save(f'poster_{content.id}.jpg', make_image(content.title, 400, 600, colors), save=False)
    content.backdrop.save(f'backdrop_{content.id}.jpg',
                          make_image(content.title, 1280, 540, (colors[1], colors[0])), save=False)
    content.save()


def add_crew(content, persons):
    director, *actors = random.sample(persons, 4)
    ContentPerson.objects.create(content=content, person=director, role='director')
    for actor in actors:
        ContentPerson.objects.create(content=content, person=actor, role='actor')


def run(clear=False):
    random.seed(42)

    if clear:
        Content.objects.all().delete()
        print('Старые фильмы удалены')

    genres = {name: Genre.objects.get_or_create(name=name, defaults={'slug': f'genre-{i}'})[0]
              for i, name in enumerate(GENRES)}
    ethnoses = {name: Ethnos.objects.get_or_create(name=name, defaults={'slug': f'ethnos-{i}'})[0]
                for i, name in enumerate(ETHNOSES)}
    countries = {name: Country.objects.get_or_create(name=name, defaults={'slug': f'country-{i}'})[0]
                 for i, name in enumerate(COUNTRIES)}
    languages = {code: Language.objects.get_or_create(code=code, defaults={'name': name})[0]
                 for name, code in LANGUAGES}
    persons = [Person.objects.get_or_create(full_name=name)[0] for name in PERSONS]

    created = 0
    for i, (title, year, genre, ethnos, country, lang, ctype, premium, featured) in enumerate(FILMS):
        if Content.objects.filter(title=title, year=year).exists():
            continue
        content = Content.objects.create(
            title=title, year=year, content_type=ctype,
            description=DESCRIPTIONS[genre],
            duration_min=random.randint(80, 125),
            age_rating=random.choice(['0+', '6+', '12+', '16+']),
            is_premium=premium, is_featured=featured,
            views_count=random.randint(50, 3000),
        )
        add_media(content, i)
        content.genres.add(genres[genre])
        content.ethnoses.add(ethnoses[ethnos])
        content.countries.add(countries[country])
        content.languages.add(languages[lang])
        add_crew(content, persons)
        created += 1

    for i, (title, year, genre, ethnos, seasons, episodes) in enumerate(SERIES):
        if Content.objects.filter(title=title, year=year).exists():
            continue
        content = Content.objects.create(
            title=title, year=year, content_type='series',
            description=DESCRIPTIONS[genre], age_rating='12+',
            views_count=random.randint(500, 5000),
        )
        add_media(content, i + 3)
        content.genres.add(genres[genre])
        content.ethnoses.add(ethnoses[ethnos])
        content.countries.add(countries['Кыргызстан'])
        content.languages.add(languages['ky'])
        add_crew(content, persons)
        for s in range(1, seasons + 1):
            season = Season.objects.create(content=content, number=s)
            for e in range(1, episodes + 1):
                Episode.objects.create(season=season, number=e, title=f'Серия {e}',
                                       duration_min=random.randint(35, 50))
        created += 1

    Plan.objects.get_or_create(name='Месяц', defaults={'duration_days': 30, 'price': 199})
    Plan.objects.get_or_create(name='Год', defaults={'duration_days': 365, 'price': 1490})

    print(f'Готово! Добавлено фильмов и сериалов: {created}')


if __name__ == '__main__':
    run(clear='--clear' in sys.argv)