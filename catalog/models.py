"""
Модели приложения 'catalog'.
Содержит три основные сущности каталога электроники:
- Category — категория товаров (Смартфоны, Ноутбуки, Аксессуары и т.д.)
- Brand — бренд / производитель (Apple, Samsung, Xiaomi и т.д.)
- Product — конкретный товар с артикулом, ценой, изображением
"""

from django.db import models
from django.urls import reverse


class Category(models.Model):
    """
    Категория товаров.
    Примеры: Смартфоны, Ноутбуки, Планшеты, Наушники, Аксессуары.
    Поле slug используется для формирования ЧПУ (человекопонятных URL).
    """

    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='URL-имя (slug)',
        help_text='Уникальное имя для URL, например: smartfony, noutbuki',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        verbose_name='Изображение',
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Возвращает URL страницы категории в каталоге."""
        return reverse('catalog:product_list_by_category', args=[self.slug])


class Brand(models.Model):
    """
    Бренд / Производитель.
    Примеры: Apple, Samsung, Xiaomi, Huawei, ASUS.
    """

    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='URL-имя (slug)',
    )
    logo = models.ImageField(
        upload_to='brands/',
        blank=True,
        verbose_name='Логотип',
    )

    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренды'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Товар — основная сущность каталога электроники.

    Связи:
    - category (FK → Category): к какой категории относится товар
    - brand (FK → Brand): какого бренда товар

    Ключевые поля:
    - sku (артикул): уникальный идентификатор товара для учёта
    - price: цена товара в гривнях
    - image: фотография товара
    - available: флаг доступности (управляется автоматически складом,
      но может быть отключён менеджером вручную)
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Категория',
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Бренд',
    )
    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Артикул',
        help_text='Уникальный код товара, например: SM-A546E',
    )
    name = models.CharField(
        max_length=300,
        verbose_name='Название',
    )
    slug = models.SlugField(
        max_length=300,
        unique=True,
        verbose_name='URL-имя (slug)',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена (₴)',
    )
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        verbose_name='Изображение',
    )
    available = models.BooleanField(
        default=True,
        verbose_name='Доступен',
        help_text='Снимите флажок, чтобы скрыть товар из каталога',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']
        # Составной индекс для быстрого поиска по категории и slug
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'available']),
        ]

    def __str__(self):
        return f'{self.name} ({self.sku})'

    def get_absolute_url(self):
        """Возвращает URL карточки товара."""
        return reverse('catalog:product_detail', args=[self.slug])


class ProductImage(models.Model):
    """Додаткові зображення товару (галерея)."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Товар',
    )
    image = models.ImageField(
        upload_to='products/gallery/',
        verbose_name='Зображення',
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Порядок',
    )

    class Meta:
        verbose_name = 'Зображення товару'
        verbose_name_plural = 'Зображення товару'
        ordering = ['order']

    def __str__(self):
        return f'{self.product.name} #{self.order}'
