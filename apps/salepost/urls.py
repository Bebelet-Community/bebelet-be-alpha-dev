from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalePostViewSet, SalePostHomeView, SalePostSimilarView


router = DefaultRouter()
router.register('', SalePostViewSet, basename="salepost")


urlpatterns = [
    path('', include(router.urls)),
    path('home/', SalePostHomeView.as_view()),
    path("similar/<int:public_id>/", SalePostSimilarView.as_view()),
]