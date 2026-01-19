from django.urls import path
from .views import CategoryListView, CategoryView, AttributeListView, AttributeView, AttributeChoiceListView, AttributeChoiceView


urlpatterns = [
    path("", CategoryListView.as_view()),
    path("<int:category_id>/", CategoryView.as_view()),
    path("attributes/", AttributeListView.as_view()),
    path("attributes/<int:attribute_id>/", AttributeView.as_view()),
    path("attribute-choices/", AttributeChoiceListView.as_view()),
    path("attribute-choices/<int:attribute_choice_id>/", AttributeChoiceView.as_view()),

]