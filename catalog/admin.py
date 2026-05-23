"""
Налаштування Django Admin для додатку 'catalog'.
Зручне відображення категорій, брендів і товарів з пошуком та фільтрацією.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Brand, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Адміністративний інтерфейс для категорій товарів."""

    list_display = ('name', 'slug', 'product_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        """Показує кількість товарів у категорії."""
        return obj.products.count()
    product_count.short_description = 'К-сть товарів'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Адміністративний інтерфейс для брендів."""

    list_display = ('name', 'slug', 'logo_preview')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def logo_preview(self, obj):
        """Прев'ю логотипу бренду у списку."""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 30px;" />',
                obj.logo.url
            )
        return '—'
    logo_preview.short_description = 'Логотип'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ('image', 'order', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 60px; border-radius: 6px;" />', obj.image.url)
        return '—'
    image_preview.short_description = "Прев'ю"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Адміністративний інтерфейс для товарів.
    Включає пошук за назвою/артикулом, фільтрацію за категорією/брендом/доступністю,
    а також прев'ю зображення товару.
    """

    list_display = (
        'sku', 'name', 'category', 'brand',
        'price', 'available', 'image_preview', 'created_at',
    )
    list_filter = ('available', 'category', 'brand', 'created_at')
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'available')
    list_per_page = 25
    inlines = [ProductImageInline]

    # Групування полів у формі редагування
    fieldsets = (
        ('Основна інформація', {
            'fields': ('sku', 'name', 'slug', 'category', 'brand'),
        }),
        ('Опис і ціна', {
            'fields': ('description', 'price', 'image'),
        }),
        ('Статус', {
            'fields': ('available',),
        }),
    )

    def image_preview(self, obj):
        """Прев'ю зображення товару у списку."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 40px;" />',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Фото'
