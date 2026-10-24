from datetime import date

import django_filters
from django.contrib.auth.password_validation import validate_password
from django.db.models import Avg, Count, Q
from rest_framework import generics, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    User, Genre, Country, Ethnos, Language, Person, Content, ContentPerson, Season, Episode,
    Favorite, WatchProgress, Rating, Review, Plan, Subscription,
)


# ===================== ПРАВА ДОСТУПА =====================

def has_subscription(user):
    # есть ли у пользователя действующая подписка
    if not user.is_authenticated:
        return False
    return user.subscriptions.filter(end_date__gte=date.today()).exists()


class IsAuthorOrReadOnly(permissions.BasePermission):
    # менять и удалять может только автор
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


# ===================== ФИЛЬТРЫ =====================

class ContentFilter(django_filters.FilterSet):
    # /api/v1/content/?type=film&genre=drama&ethnos=kyrgyz&year_min=1990
    type = django_filters.CharFilter(field_name='content_type')
    genre = django_filters.CharFilter(field_name='genres__slug')
    country = django_filters.CharFilter(field_name='countries__slug')
    ethnos = django_filters.CharFilter(field_name='ethnoses__slug')
    language = django_filters.CharFilter(field_name='languages__code')
    year_min = django_filters.NumberFilter(field_name='year', lookup_expr='gte')
    year_max = django_filters.NumberFilter(field_name='year', lookup_expr='lte')
    age = django_filters.CharFilter(field_name='age_rating')
    premium = django_filters.BooleanFilter(field_name='is_premium')

    class Meta:
        model = Content
        fields = []


# ===================== СЕРИАЛИЗАТОРЫ =====================

# ---------- ПОЛЬЗОВАТЕЛИ ----------

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


# ---------- СПРАВОЧНИКИ ----------

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


# ---------- КАТАЛОГ ----------

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


# ---------- ПРОСМОТР ----------

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


# ---------- ПОДПИСКИ ----------

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


# ===================== VIEWS =====================

# ---------- ПОЛЬЗОВАТЕЛИ ----------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Пароль изменён'})


# ---------- СПРАВОЧНИКИ ----------
# без пагинации — нужны целиком для фильтров на фронте

class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    pagination_class = None


class EthnosViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ethnos.objects.all()
    serializer_class = EthnosSerializer
    pagination_class = None


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    pagination_class = None


class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


# ---------- КАТАЛОГ ----------

class ContentViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'slug'
    filterset_class = ContentFilter
    search_fields = ['title', 'original_title', 'description', 'persons__person__full_name']
    ordering_fields = ['created_at', 'rating', 'views_count', 'title', 'year']
    ordering = ['-created_at']

    def get_queryset(self):
        # средняя оценка и число голосов считаются прямо в запросе
        return (
            Content.objects.filter(is_published=True)
            .annotate(rating=Avg('ratings__score'), votes=Count('ratings', distinct=True))
            .prefetch_related('genres', 'countries', 'ethnoses', 'languages', 'persons__person')
            .distinct()
        )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ContentDetailSerializer
        return ContentListSerializer

    @action(detail=False)
    def featured(self, request):
        # баннер на главной
        contents = self.get_queryset().filter(is_featured=True)[:5]
        return Response(ContentListSerializer(contents, many=True, context={'request': request}).data)

    @action(detail=True)
    def similar(self, request, slug=None):
        # похожие — совпадают жанры или народ
        content = self.get_object()
        similar = (
            self.get_queryset()
            .filter(Q(genres__in=content.genres.all()) | Q(ethnoses__in=content.ethnoses.all()))
            .exclude(id=content.id)[:10]
        )
        return Response(ContentListSerializer(similar, many=True, context={'request': request}).data)

    @action(detail=True)
    def seasons(self, request, slug=None):
        content = self.get_object()
        seasons = content.seasons.prefetch_related('episodes')
        return Response(SeasonSerializer(seasons, many=True).data)

    @action(detail=True)
    def stream(self, request, slug=None):
        content = self.get_object()
        if content.is_premium and not has_subscription(request.user):
            return Response({'detail': 'Нужна подписка'}, status=status.HTTP_403_FORBIDDEN)
        if not content.video_file:
            return Response({'detail': 'Видео не загружено'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'url': request.build_absolute_uri(content.video_file.url)})

    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def rating(self, request, slug=None):
        content = self.get_object()
        serializer = RatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # если оценка уже есть — обновляем, иначе создаём
        Rating.objects.update_or_create(
            user=request.user, content=content,
            defaults={'score': serializer.validated_data['score']},
        )
        return Response({'score': serializer.validated_data['score']})

    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, slug=None):
        content = self.get_object()
        if request.method == 'POST':
            if not request.user.is_authenticated:
                return Response({'detail': 'Войдите, чтобы оставить отзыв'},
                                status=status.HTTP_401_UNAUTHORIZED)
            serializer = ReviewSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user, content=content)  # статус pending по умолчанию
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        reviews = content.reviews.filter(status='approved').select_related('user')
        return Response(ReviewSerializer(reviews, many=True).data)


class EpisodeStreamView(generics.GenericAPIView):
    serializer_class = StreamSerializer

    def get(self, request, pk):
        episode = generics.get_object_or_404(Episode, pk=pk, season__content__is_published=True)
        if episode.season.content.is_premium and not has_subscription(request.user):
            return Response({'detail': 'Нужна подписка'}, status=status.HTTP_403_FORBIDDEN)
        if not episode.video_file:
            return Response({'detail': 'Видео не загружено'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'url': request.build_absolute_uri(episode.video_file.url)})


class SearchSuggestView(generics.GenericAPIView):
    # подсказки в строке поиска
    serializer_class = SuggestSerializer
    pagination_class = None

    def get(self, request):
        q = request.query_params.get('q', '')
        if len(q) < 2:
            return Response([])
        contents = Content.objects.filter(
            Q(title__icontains=q) | Q(original_title__icontains=q),
            is_published=True,
        )[:8]
        return Response([{'title': c.title, 'slug': c.slug, 'year': c.year} for c in contents])


# ---------- ПРОСМОТР ----------

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']
    lookup_field = 'content_id'  # удаляем по id фильма: DELETE /favorites/5/

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('content').order_by('-added_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HistoryView(generics.ListAPIView):
    serializer_class = WatchProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WatchProgress.objects.filter(user=self.request.user).select_related('content')


class ContinueWatchingView(generics.ListAPIView):
    # «Продолжить просмотр» — начатые, но не досмотренные
    serializer_class = WatchProgressSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return (WatchProgress.objects
                .filter(user=self.request.user, is_finished=False, position_sec__gt=0)
                .select_related('content')[:10])


class SaveProgressView(generics.GenericAPIView):
    serializer_class = SaveProgressSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SaveProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        progress, created = WatchProgress.objects.update_or_create(
            user=request.user,
            content=data['content'],
            episode=data.get('episode'),
            defaults={'position_sec': data['position_sec'], 'duration_sec': data['duration_sec']},
        )
        # просмотр считаем, когда пользователь впервые начал смотреть
        if created:
            content = data['content']
            content.views_count += 1
            content.save(update_fields=['views_count'])

        return Response(WatchProgressSerializer(progress, context={'request': request}).data)


class ReviewDeleteView(generics.DestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]


# ---------- ПОДПИСКИ ----------

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    pagination_class = None


class SubscriptionCreateView(generics.CreateAPIView):
    # учебная «оплата» — просто создаём подписку
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # если подписка ещё действует, новая начнётся после неё
        last = self.request.user.subscriptions.filter(end_date__gte=date.today()).order_by('-end_date').first()
        start = last.end_date if last else date.today()
        serializer.save(user=self.request.user, start_date=start)


class MySubscriptionView(generics.GenericAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = request.user.subscriptions.filter(end_date__gte=date.today()).order_by('-end_date').first()
        if not subscription:
            return Response({'detail': 'Нет активной подписки'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SubscriptionSerializer(subscription).data)


