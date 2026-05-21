"""
Модели приложения 'warehouse' — складской учёт.

Это КЛЮЧЕВАЯ часть дипломного проекта, демонстрирующая автоматизацию
бизнес-процесса учёта товаров на складе.

Схема работы:
1. Менеджер создаёт Поставку (Supply) от Поставщика (Supplier)
2. В поставке указываются позиции (SupplyItem): какой товар и сколько штук пришло
3. При сохранении поставки остаток на складе (Stock) АВТОМАТИЧЕСКИ увеличивается
4. При оформлении заказа клиентом остаток АВТОМАТИЧЕСКИ уменьшается (Шаг 5)
"""

from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator

from catalog.models import Product


class Supplier(models.Model):
    """
    Поставщик товаров.
    Хранит информацию о компаниях, которые поставляют электронику в магазин.
    """

    name = models.CharField(
        max_length=300,
        verbose_name='Название компании',
    )
    contact_person = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Контактное лицо',
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон',
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email',
    )
    address = models.TextField(
        blank=True,
        verbose_name='Адрес',
    )

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['name']

    def __str__(self):
        return self.name


class Supply(models.Model):
    """
    Поставка (приход товара на склад).

    Каждая поставка связана с конкретным поставщиком и содержит
    одну или несколько позиций (SupplyItem).

    Статусы поставки:
    - NEW (Новая) — только создана, товар ещё не пришёл
    - RECEIVED (Получена) — товар получен, остатки на складе обновлены
    - CANCELLED (Отменена) — поставка отменена
    """

    class Status(models.TextChoices):
        NEW = 'new', 'Нова'
        RECEIVED = 'received', 'Отримана'
        CANCELLED = 'cancelled', 'Скасована'

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='supplies',
        verbose_name='Поставщик',
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name='Статус',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    received_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата получения',
        help_text='Заполняется автоматически при смене статуса на "Получена"',
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примечания',
    )

    class Meta:
        verbose_name = 'Поставка'
        verbose_name_plural = 'Поставки'
        ordering = ['-created_at']

    def __str__(self):
        return f'Поставка #{self.pk} от {self.supplier} ({self.get_status_display()})'

    @property
    def total_items(self):
        """Общее количество единиц товара в поставке."""
        return sum(item.quantity for item in self.items.all())


class SupplyItem(models.Model):
    """
    Позиция в поставке — конкретный товар и его количество.

    Пример: в поставке #5 от Samsung пришло:
    - Galaxy S24 — 10 шт. по 75 000 ₴
    - Galaxy Buds — 20 шт. по 8 000 ₴

    При смене статуса поставки на "Получена" данные из SupplyItem
    используются для обновления складских остатков (Stock).
    """

    supply = models.ForeignKey(
        Supply,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Поставка',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='supply_items',
        verbose_name='Товар',
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)],
        help_text='Количество единиц товара в поставке',
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Закупочная цена (₴)',
        help_text='Цена за единицу товара у поставщика',
    )

    class Meta:
        verbose_name = 'Позиция поставки'
        verbose_name_plural = 'Позиции поставки'

    def __str__(self):
        return f'{self.product.name} × {self.quantity} шт.'

    @property
    def total_cost(self):
        """Общая стоимость позиции = цена × количество."""
        return self.purchase_price * self.quantity


class Stock(models.Model):
    """
    Текущий остаток товара на складе.

    КЛЮЧЕВАЯ модель для автоматизации:
    - Связь OneToOne с Product — у каждого товара ровно одна запись остатка
    - quantity увеличивается при приёмке поставки (Supply → RECEIVED)
    - quantity уменьшается при оформлении заказа клиентом (Order → Шаг 5)
    - Если quantity == 0, кнопка покупки на сайте блокируется

    Метод update_stock() — атомарная операция обновления остатка
    с использованием F-выражений Django для безопасности
    при параллельных запросах.
    """

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='stock',
        verbose_name='Товар',
    )
    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name='Остаток на складе',
        help_text='Текущее количество единиц товара на складе',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Последнее обновление',
    )

    class Meta:
        verbose_name = 'Остаток на складе'
        verbose_name_plural = 'Остатки на складе'
        ordering = ['product__name']
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name='stock_quantity_non_negative',
            )
        ]

    def __str__(self):
        return f'{self.product.name} — {self.quantity} шт.'
