"""
Моделі додатку 'warehouse' — складський облік.

Це КЛЮЧОВА частина дипломного проекту, що демонструє автоматизацію
бізнес-процесу обліку товарів на складі.

Схема роботи:
1. Менеджер створює Поставку (Supply) від Постачальника (Supplier)
2. У поставці вказуються позиції (SupplyItem): який товар і скільки штук прийшло
3. При збереженні поставки залишок на складі (Stock) АВТОМАТИЧНО збільшується
4. При оформленні замовлення клієнтом залишок АВТОМАТИЧНО зменшується (Крок 5)
"""

from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator

from catalog.models import Product


class Supplier(models.Model):
    """
    Постачальник товарів.
    Зберігає інформацію про компанії, які постачають електроніку до магазину.
    """

    name = models.CharField(
        max_length=300,
        verbose_name='Назва компанії',
    )
    contact_person = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Контактна особа',
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
        verbose_name='Адреса',
    )

    class Meta:
        verbose_name = 'Постачальник'
        verbose_name_plural = 'Постачальники'
        ordering = ['name']

    def __str__(self):
        return self.name


class Supply(models.Model):
    """
    Поставка (прихід товару на склад).

    Кожна поставка пов'язана з конкретним постачальником і містить
    одну або кілька позицій (SupplyItem).

    Статуси поставки:
    - NEW (Нова) — щойно створена, товар ще не прийшов
    - RECEIVED (Отримана) — товар отримано, залишки на складі оновлено
    - CANCELLED (Скасована) — поставку скасовано
    """

    class Status(models.TextChoices):
        NEW = 'new', 'Нова'
        RECEIVED = 'received', 'Отримана'
        CANCELLED = 'cancelled', 'Скасована'

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='supplies',
        verbose_name='Постачальник',
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name='Статус',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення',
    )
    received_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата отримання',
        help_text='Заповнюється автоматично при зміні статусу на "Отримана"',
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Примітки',
    )

    class Meta:
        verbose_name = 'Поставка'
        verbose_name_plural = 'Поставки'
        ordering = ['-created_at']

    def __str__(self):
        return f'Поставка #{self.pk} від {self.supplier} ({self.get_status_display()})'

    @property
    def total_items(self):
        """Загальна кількість одиниць товару в поставці."""
        return sum(item.quantity for item in self.items.all())


class SupplyItem(models.Model):
    """
    Позиція в поставці — конкретний товар та його кількість.

    Приклад: у поставці #5 від Samsung прийшло:
    - Galaxy S24 — 10 шт. по 75 000 ₴
    - Galaxy Buds — 20 шт. по 8 000 ₴

    При зміні статусу поставки на "Отримана" дані з SupplyItem
    використовуються для оновлення складських залишків (Stock).
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
        verbose_name='Кількість',
        validators=[MinValueValidator(1)],
        help_text='Кількість одиниць товару в поставці',
    )
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Закупівельна ціна (₴)',
        help_text='Ціна за одиницю товару у постачальника',
    )

    class Meta:
        verbose_name = 'Позиція поставки'
        verbose_name_plural = 'Позиції поставки'

    def __str__(self):
        return f'{self.product.name} × {self.quantity} шт.'

    @property
    def total_cost(self):
        """Загальна вартість позиції = ціна × кількість."""
        return self.purchase_price * self.quantity


class Stock(models.Model):
    """
    Поточний залишок товару на складі.

    КЛЮЧОВА модель для автоматизації:
    - Зв'язок OneToOne з Product — у кожного товару рівно один запис залишку
    - quantity збільшується при прийманні поставки (Supply → RECEIVED)
    - quantity зменшується при оформленні замовлення клієнтом (Order → Крок 5)
    - Якщо quantity == 0, кнопка покупки на сайті блокується

    Метод update_stock() — атомарна операція оновлення залишку
    з використанням F-виразів Django для безпеки
    при паралельних запитах.
    """

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='stock',
        verbose_name='Товар',
    )
    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name='Залишок на складі',
        help_text='Поточна кількість одиниць товару на складі',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Останнє оновлення',
    )

    class Meta:
        verbose_name = 'Залишок на складі'
        verbose_name_plural = 'Залишки на складі'
        ordering = ['product__name']
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name='stock_quantity_non_negative',
            )
        ]

    def __str__(self):
        return f'{self.product.name} — {self.quantity} шт.'
