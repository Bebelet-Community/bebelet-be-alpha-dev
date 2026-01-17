from django.contrib import admin
from django.urls import path,include

from rest_framework.permissions import AllowAny

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/schema/', SpectacularAPIView.as_view(permission_classes=[AllowAny], authentication_classes=[]), name='schema', ),
    path('swagger/docs/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[AllowAny], authentication_classes=[]), name='swagger-ui'),
    path('swagger/redocs/', SpectacularRedocView.as_view(url_name='schema', permission_classes=[AllowAny], authentication_classes=[]), name='redoc'),

    path("api/auth/", include("apps.authentication.urls")),
    path("api/category/", include("apps.category.urls")),
]
