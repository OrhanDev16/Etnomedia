from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import (
    User, Genre, Country, Ethnos, Language, Person, Content, ContentPerson, Season, Episode,
    Favorite, WatchProgress, Rating, Review, Plan, Subscription,
)
from .permissions import has_subscription


# ===================== ПОЛЬЗОВАТЕЛИ =====================

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Пароли не совпадают'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    has_subscription = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'avatar', 'date_joined',
                  'has_subscription']
        read_only_fields = ['email', 'date_joined']

    def get_has_subscription(self, obj):
        return has_subscription(obj)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль')
        return value


# ===================== СПРАВОЧНИКИ =====================

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug']


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'slug']


class EthnosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ethnos
        fields = ['id', 'name', 'slug', 'description']


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'code']


# ===================== КАТАЛОГ =====================

class ContentListSerializer(serializers.ModelSerializer):
    # для карточек в каталоге — только главное
    rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Content
        fields = ['id', 'title', 'slug', 'content_type', 'year', 'age_rating', 'poster',
                  'is_premium', 'rating']


class ContentPersonSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='person.id')
    full_name = serializers.CharField(source='person.full_name')
    photo = serializers.ImageField(source='person.photo')

    class Meta:
        model = ContentPerson
        fields = ['id', 'full_name', 'photo', 'role', 'character_name']


class ContentDetailSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True)
    countries = CountrySerializer(many=True)
    ethnoses = EthnosSerializer(many=True)
    languages = LanguageSerializer(many=True)
    persons = ContentPersonSerializer(many=True)
    rating = serializers.FloatField(read_only=True)
    votes = serializers.IntegerField(read_only=True)
    is_favorite = serializers.SerializerMethodField()
    my_rating = serializers.SerializerMethodField()

    class Meta:
        model = Content
        # video_file не отдаём — ссылка на видео только через /stream/
        fields = ['id', 'title', 'original_title', 'slug', 'content_type', 'description', 'year',
                  'duration_min', 'age_rating', 'poster', 'backdrop', 'trailer', 'is_premium',
                  'views_count', 'genres', 'countries', 'ethnoses', 'languages', 'persons',
                  'rating', 'votes', 'is_favorite', 'my_rating']

    def get_is_favorite(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.favorite_set.filter(user=user).exists()

    def get_my_rating(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return None
        rating = obj.ratings.filter(user=user).first()
        return rating.score if rating else None


class EpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Episode
        fields = ['id', 'number', 'title', 'description', 'duration_min']


class SeasonSerializer(serializers.ModelSerializer):
    episodes = EpisodeSerializer(many=True)

    class Meta:
        model = Season
        fields = ['id', 'number', 'title', 'episodes']


class PersonSerializer(serializers.ModelSerializer):
    works = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = ['id', 'full_name', 'photo', 'bio', 'birth_date', 'works']

    def get_works(self, obj):
        # фильмография: фильм + роль
        result = []
        for work in obj.works.filter(content__is_published=True).select_related('content'):
            result.append({
                'title': work.content.title,
                'slug': work.content.slug,
                'year': work.content.year,
                'role': work.role,
            })
        return result


# ===================== ПРОСМОТР =====================

class FavoriteSerializer(serializers.ModelSerializer):
    content = ContentListSerializer(read_only=True)
    content_id = serializers.PrimaryKeyRelatedField(
        queryset=Content.objects.filter(is_published=True), source='content', write_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'content', 'content_id', 'added_at']

    def validate_content_id(self, value):
        user = self.context['request'].user
        if Favorite.objects.filter(user=user, content=value).exists():
            raise serializers.ValidationError('Уже в избранном')
        return value


class WatchProgressSerializer(serializers.ModelSerializer):
    content = ContentListSerializer(read_only=True)
    percent = serializers.SerializerMethodField()

    class Meta:
        model = WatchProgress
        fields = ['id', 'content', 'episode', 'position_sec', 'duration_sec', 'percent',
                  'is_finished', 'updated_at']

    def get_percent(self, obj):
        if not obj.duration_sec:
            return 0
        return min(100, round(obj.position_sec * 100 / obj.duration_sec))


class StreamSerializer(serializers.Serializer):
    url = serializers.URLField()


class SuggestSerializer(serializers.Serializer):
    title = serializers.CharField()
    slug = serializers.CharField()
    year = serializers.IntegerField()


class SaveProgressSerializer(serializers.Serializer):
    content = serializers.PrimaryKeyRelatedField(queryset=Content.objects.all())
    episode = serializers.PrimaryKeyRelatedField(queryset=Episode.objects.all(), required=False,
                                                 allow_null=True)
    position_sec = serializers.IntegerField(min_value=0)
    duration_sec = serializers.IntegerField(min_value=0)


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['score']

    def validate_score(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError('Оценка должна быть от 1 до 10')
        return value


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'text', 'status', 'created_at']
        read_only_fields = ['status']


# ===================== ПОДПИСКИ =====================

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'duration_days', 'price']


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(is_active=True), source='plan', write_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'plan_id', 'start_date', 'end_date', 'is_active']
        read_only_fields = ['start_date', 'end_date']

    def get_is_active(self, obj):
        return obj.is_active()