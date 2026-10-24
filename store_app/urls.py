from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('content', views.ContentViewSet, basename='content')
router.register('genres', views.GenreViewSet)
router.register('countries', views.CountryViewSet)
router.register('ethnoses', views.EthnosViewSet)
router.register('languages', views.LanguageViewSet)
router.register('persons', views.PersonViewSet)
router.register('favorites', views.FavoriteViewSet, basename='favorites')
router.register('plans', views.PlanViewSet)

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view()),
    path('users/me/', views.MeView.as_view()),
    path('users/me/change-password/', views.ChangePasswordView.as_view()),

    path('episodes/<int:pk>/stream/', views.EpisodeStreamView.as_view()),
    path('search/suggest/', views.SearchSuggestView.as_view()),

    path('history/', views.HistoryView.as_view()),
    path('history/continue/', views.ContinueWatchingView.as_view()),
    path('progress/', views.SaveProgressView.as_view()),
    path('reviews/<int:pk>/', views.ReviewDeleteView.as_view()),

    path('subscriptions/', views.SubscriptionCreateView.as_view()),
    path('subscriptions/me/', views.MySubscriptionView.as_view()),

    path('', include(router.urls)),
]
