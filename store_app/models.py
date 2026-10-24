from datetime import date, timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.text import slugify


# ===================== ПОЛЬЗОВАТЕЛИ =====================

# свой менеджер нужен, чтобы createsuperuser спрашивал email, а не username
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Нужно указать email')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    USERNAME_FIELD = 'email'  # вход по email
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


# ===================== КАТАЛОГ =====================

class Genre(models.Model):
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'

    def __str__(self):
        return self.name


class Ethnos(models.Model):
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Народ'
        verbose_name_plural = 'Народы'

    def __str__(self):
        return self.name


class Language(models.Model):
    name = models.CharField('Название', max_length=100)
    code = models.CharField('Код', max_length=10)  # ky, ru, en

    class Meta:
        verbose_name = 'Язык'
        verbose_name_plural = 'Языки'

    def __str__(self):
        return self.name


class Person(models.Model):
    full_name = models.CharField('Имя', max_length=200)
    photo = models.ImageField('Фото', upload_to='persons/', blank=True, null=True)
    bio = models.TextField('Биография', blank=True)
    birth_date = models.DateField('Дата рождения', blank=True, null=True)

    class Meta:
        verbose_name = 'Персона'
        verbose_name_plural = 'Персоны'

    def __str__(self):
        return self.full_name


class Content(models.Model):
    TYPE_CHOICES = [
        ('film', 'Фильм'),
        ('series', 'Сериал'),
        ('cartoon', 'Мультфильм'),
        ('documentary', 'Документальный'),
    ]
    AGE_CHOICES = [
        ('0+', '0+'),
        ('6+', '6+'),
        ('12+', '12+'),
        ('16+', '16+'),
        ('18+', '18+'),
    ]

    title = models.CharField('Название', max_length=255)
    original_title = models.CharField('Оригинальное название', max_length=255, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    content_type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES, default='film')
    description = models.TextField('Описание', blank=True)
    year = models.IntegerField('Год')
    duration_min = models.IntegerField('Длительность (мин)', blank=True, null=True)
    age_rating = models.CharField('Возраст', max_length=3, choices=AGE_CHOICES, default='0+')

    poster = models.ImageField('Постер', upload_to='posters/', blank=True, null=True)
    backdrop = models.ImageField('Фон', upload_to='backdrops/', blank=True, null=True)
    trailer = models.FileField('Трейлер', upload_to='trailers/', blank=True, null=True)
    video_file = models.FileField('Видео', upload_to='videos/', blank=True, null=True)

    genres = models.ManyToManyField(Genre, blank=True, verbose_name='Жанры')
    countries = models.ManyToManyField(Country, blank=True, verbose_name='Страны')
    ethnoses = models.ManyToManyField(Ethnos, blank=True, verbose_name='Народы')
    languages = models.ManyToManyField(Language, blank=True, verbose_name='Языки')

    is_premium = models.BooleanField('Премиум', default=False)
    is_featured = models.BooleanField('На главной', default=False)
    is_published = models.BooleanField('Опубликовано', default=True)
    views_count = models.IntegerField('Просмотры', default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Фильм / сериал'
        verbose_name_plural = 'Фильмы и сериалы'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # если slug не заполнили, делаем из названия и года
        if not self.slug:
            self.slug = slugify(f'{self.title}-{self.year}', allow_unicode=True)
        super().save(*args, **kwargs)


class ContentPerson(models.Model):
    ROLE_CHOICES = [
        ('director', 'Режиссёр'),
        ('actor', 'Актёр'),
        ('writer', 'Сценарист'),
    ]

    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='persons')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='works')
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES)
    character_name = models.CharField('Персонаж', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Съёмочная группа'

    def __str__(self):
        return f'{self.person} ({self.role})'


class Season(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='seasons')
    number = models.IntegerField('Номер сезона')
    title = models.CharField('Название', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Сезон'
        verbose_name_plural = 'Сезоны'
        ordering = ['number']
        unique_together = ['content', 'number']

    def __str__(self):
        return f'{self.content.title} - сезон {self.number}'


class Episode(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='episodes')
    number = models.IntegerField('Номер серии')
    title = models.CharField('Название', max_length=255, blank=True)
    description = models.TextField('Описание', blank=True)
    duration_min = models.IntegerField('Длительность (мин)', blank=True, null=True)
    video_file = models.FileField('Видео', upload_to='episodes/', blank=True, null=True)

    class Meta:
        verbose_name = 'Эпизод'
        verbose_name_plural = 'Эпизоды'
        ordering = ['number']
        unique_together = ['season', 'number']

    def __str__(self):
        return f'{self.season} - серия {self.number}'


# ===================== ПРОСМОТР =====================

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ['user', 'content']  # один фильм нельзя добавить дважды

    def __str__(self):
        return f'{self.user} - {self.content}'


class WatchProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history')
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, blank=True, null=True)  # только для сериалов
    position_sec = models.IntegerField('Позиция (сек)', default=0)
    duration_sec = models.IntegerField('Длительность (сек)', default=0)
    is_finished = models.BooleanField('Досмотрено', default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Прогресс просмотра'
        verbose_name_plural = 'История просмотров'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user} - {self.content}'

    def save(self, *args, **kwargs):
        # считаем досмотренным если прошли 95%
        if self.duration_sec and self.position_sec >= self.duration_sec * 0.95:
            self.is_finished = True
        super().save(*args, **kwargs)


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='ratings')
    score = models.IntegerField('Оценка')  # от 1 до 10, проверяем в сериализаторе

    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        unique_together = ['user', 'content']

    def __str__(self):
        return f'{self.user} - {self.content}: {self.score}'


class Review(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На модерации'),
        ('approved', 'Одобрен'),
        ('rejected', 'Отклонён'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField('Текст', max_length=2000)
    status = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Отзыв от {self.user}'


# ===================== ПОДПИСКИ =====================

class Plan(models.Model):
    name = models.CharField('Название', max_length=100)
    duration_days = models.IntegerField('Срок (дней)')
    price = models.DecimalField('Цена', max_digits=8, decimal_places=2)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'

    def __str__(self):
        return self.name


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    start_date = models.DateField('Начало', default=date.today)
    end_date = models.DateField('Окончание', blank=True, null=True)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} - {self.plan}'

    def save(self, *args, **kwargs):
        # дата окончания = начало + срок тарифа
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    def is_active(self):
        return self.end_date >= date.today()



