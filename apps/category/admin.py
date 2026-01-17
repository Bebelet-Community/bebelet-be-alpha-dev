from django.contrib import admin
from .models import Category, UsageRange, Brand, Attribute, AttributeChoice

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",) 