"""
Настройка Django Admin для приложения 'catalog'.
Удобное отображение категорий, брендов и товаров с поиском и фильтрацией.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Brand, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Административный интерфейс для категорий товаров."""

    list_display = ('name', 'slug', 'product_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        """Показывает количество товаров в категории."""
        return obj.products.count()
    product_count.short_description = 'Кол-во товаров'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Административный интерфейс для брендов."""

    list_display = ('name', 'slug', 'logo_preview')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def logo_preview(self, obj):
        """Превью логотипа бренда в списке."""
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
    image_preview.short_description = 'Превью'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для товаров.
    Включает поиск по названию/артикулу, фильтрацию по категории/бренду/доступности,
    а также превью изображения товара.
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

    # Группировка полей в форме редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('sku', 'name', 'slug', 'category', 'brand'),
        }),
        ('Описание и цена', {
            'fields': ('description', 'price', 'image'),
        }),
        ('Статус', {
            'fields': ('available',),
        }),
    )

    def image_preview(self, obj):
        """Превью изображения товара в списке."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 40px;" />',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Фото'
