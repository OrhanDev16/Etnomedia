import django_filters

from .models import Content


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