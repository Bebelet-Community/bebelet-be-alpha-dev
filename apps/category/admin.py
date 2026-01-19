from django.contrib import admin
from .models import Category, UsageRange, Brand, Attribute, AttributeChoice

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",) 

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ("display_name",)

@admin.register(AttributeChoice)
class AttributeChoiceAdmin(admin.ModelAdmin):
    list_display = ("attribute",)