"""
Моделі додатку 'catalog'.
Містить три основні сутності каталогу електроніки:
- Category — категорія товарів (Смартфони, Ноутбуки, Аксесуари тощо)
- Brand — бренд / виробник (Apple, Samsung, Xiaomi тощо)
- Product — конкретний товар з артикулом, ціною, зображенням
"""

from django.db import models
from django.urls import reverse


class Category(models.Model):
    """
    Категорія товарів.
    Приклади: Смартфони, Ноутбуки, Планшети, Навушники, Аксесуари.
    Поле slug використовується для формування ЧПУ (зрозумілих URL).
    """

    name = models.CharField(
        max_length=200,
        verbose_name='Назва',
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='URL-ім\'я (slug)',
        help_text='Унікальне ім\'я для URL, наприклад: smartfony, noutbuki',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Опис',
    )
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        verbose_name='Зображення',
    )

    class Meta:
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Повертає URL сторінки категорії в каталозі."""
        return reverse('catalog:product_list_by_category', args=[self.slug])


class Brand(models.Model):
    """
    Бренд / Виробник.
    Приклади: Apple, Samsung, Xiaomi, Huawei, ASUS.
    """

    name = models.CharField(
        max_length=200,
        verbose_name='Назва',
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='URL-ім\'я (slug)',
    )
    logo = models.ImageField(
        upload_to='brands/',
        blank=True,
        verbose_name='Логотип',
    )

    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренди'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Товар — основна сутність каталогу електроніки.

    Зв'язки:
    - category (FK → Category): до якої категорії належить товар
    - brand (FK → Brand): якого бренду товар

    Ключові поля:
    - sku (артикул): унікальний ідентифікатор товару для обліку
    - price: ціна товару у гривнях
    - image: фотографія товару
    - available: прапор доступності (керується автоматично складом,
      але може бути вимкнений менеджером вручну)
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Категорія',
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
        help_text='Унікальний код товару, наприклад: SM-A546E',
    )
    name = models.CharField(
        max_length=300,
        verbose_name='Назва',
    )
    slug = models.SlugField(
        max_length=300,
        unique=True,
        verbose_name='URL-ім\'я (slug)',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Опис',
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Ціна (₴)',
    )
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        verbose_name='Зображення',
    )
    specs = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Характеристики',
        help_text='Словник "назва": "значення", наприклад: {"Дисплей": "6.1 OLED"}',
    )
    available = models.BooleanField(
        default=True,
        verbose_name='Доступний',
        help_text='Зніміть прапорець, щоб приховати товар з каталогу',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата додавання',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата оновлення',
    )

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товари'
        ordering = ['-created_at']
        # Складений індекс для швидкого пошуку за категорією та slug
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'available']),
        ]

    def __str__(self):
        return f'{self.name} ({self.sku})'

    def get_absolute_url(self):
        """Повертає URL картки товару."""
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
