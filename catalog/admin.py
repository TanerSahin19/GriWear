
from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_new", "is_active", "created_at")
    list_filter = ("is_new", "is_active", "category")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
