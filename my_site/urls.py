from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

admin.site.site_header = 'Этномедиа — администрирование'
admin.site.site_title = 'Этномедиа'

urlpatterns = [
    path('admin/', admin.site.urls),

    # API кинотеатра
    path('api/v1/', include('store_app.urls')),

    # JWT
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # документация API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
