from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register('', views.SalePostViewSet, basename="salepost")
#router.register('similar', views.SalePostSimilarViewSet, basename="similar")
#router.register('home', views.SalePostHomeViewSet, basename="home")


urlpatterns = [
    path('', include(router.urls)),
]