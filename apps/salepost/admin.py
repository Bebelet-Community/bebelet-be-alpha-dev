from django.contrib import admin
from apps.salepost.models import SalePost, SalePostAttribute, Image

@admin.register(SalePost)
class SalepostAdmin(admin.ModelAdmin):
    list_display = ("post_id", "post_status", "post_title", "product_price")

@admin.register(SalePostAttribute)
class SalePostAttributeAdmin(admin.ModelAdmin):
    list_display = ("salepost", "attribute", "value")

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("id", 'img', 'related_post')