from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User, Genre, Country, Ethnos, Language, Person, Content, ContentPerson, Season, Episode,
    Favorite, WatchProgress, Rating, Review, Plan, Subscription,
)

# ===================== ПОЛЬЗОВАТЕЛИ =====================

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'is_staff', 'date_joined']
    search_fields = ['email', 'username']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('username', 'first_name', 'last_name', 'avatar')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2')}),
    )


# ===================== КАТАЛОГ =====================

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ethnos)
class EthnosAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'birth_date']
    search_fields = ['full_name']


class ContentPersonInline(admin.TabularInline):
    model = ContentPerson
    extra = 1


class SeasonInline(admin.TabularInline):
    model = Season
    extra = 0
    show_change_link = True  # ссылка на сезон, там добавляются серии


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'year', 'is_premium', 'is_published', 'views_count']
    list_filter = ['content_type', 'is_premium', 'is_published', 'genres']
    search_fields = ['title', 'original_title']
    list_editable = ['is_premium', 'is_published']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['genres', 'countries', 'ethnoses', 'languages']
    inlines = [ContentPersonInline, SeasonInline]


class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 1


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'content', 'number']
    inlines = [EpisodeInline]


# ===================== ПРОСМОТР =====================

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'added_at']


@admin.register(WatchProgress)
class WatchProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'episode', 'position_sec', 'is_finished', 'updated_at']
    list_filter = ['is_finished']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'score']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'status', 'created_at']
    list_filter = ['status']
    list_editable = ['status']
    actions = ['approve', 'reject']

    @admin.action(description='Одобрить')
    def approve(self, request, queryset):
        queryset.update(status='approved')

    @admin.action(description='Отклонить')
    def reject(self, request, queryset):
        queryset.update(status='rejected')


# ===================== ПОДПИСКИ =====================

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_days', 'price', 'is_active']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'start_date', 'end_date']
    list_filter = ['plan']