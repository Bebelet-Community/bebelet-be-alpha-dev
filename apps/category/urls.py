from django.urls import path
from .views import CategoryListView, CategoryView


urlpatterns = [
    path("list/", CategoryListView.as_view()),
    path("<int:id>/", CategoryView.as_view())
]