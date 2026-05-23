"""
Моделі додатку 'orders'.

Замовлення (Order) — оформлена клієнтом покупка, що містить одну або
кілька позицій (OrderItem). При створенні замовлення товар автоматично
списується зі складу (див. orders/signals.py — Крок 5).
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from catalog.models import Product


class Order(models.Model):
    """
    Замовлення клієнта.

    Статуси життєвого циклу замовлення:
    - NEW (Новий) — клієнт оформив замовлення, товар списано зі складу
    - PROCESSING (В обробці) — менеджер взяв замовлення в роботу
    - SHIPPED (Відправлений) — замовлення передано в доставку
    - DELIVERED (Доставлений) — клієнт отримав замовлення
    - CANCELLED (Скасований) — замовлення скасовано (товар повертається на склад)
    """

    class Status(models.TextChoices):
        NEW = 'new', 'Новий'
        PROCESSING = 'processing', 'В обробці'
        SHIPPED = 'shipped', 'Відправлено'
        DELIVERED = 'delivered', 'Доставлено'
        CANCELLED = 'cancelled', 'Скасовано'

    # Зв'язок з користувачем (може бути NULL для незареєстрованих покупців)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Користувач',
    )

    # Контактні дані для доставки
    first_name = models.CharField(
        max_length=100,
        verbose_name="Ім'я",
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name='Прізвище',
    )
    email = models.EmailField(
        verbose_name='Email',
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='Телефон',
    )
    address = models.TextField(
        verbose_name='Адреса доставки',
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
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата оновлення',
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Коментар до замовлення',
    )

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'
        ordering = ['-created_at']

    def __str__(self):
        return f'Замовлення #{self.pk} — {self.first_name} {self.last_name}'

    @property
    def total_cost(self):
        """Загальна вартість замовлення = сума вартостей усіх позицій."""
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    """
    Позиція в замовленні — конкретний товар, його кількість і ціна
    на момент оформлення замовлення.

    ВАЖЛИВО: ціна фіксується в момент оформлення замовлення (поле price),
    щоб зміна ціни товару в каталозі не впливала на вже оформлені замовлення.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Замовлення',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Товар',
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Ціна на момент замовлення (₴)',
        help_text='Фіксується при оформленні, не залежить від поточної ціни товару',
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Кількість',
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = 'Позиція замовлення'
        verbose_name_plural = 'Позиції замовлення'

    def __str__(self):
        return f'{self.product.name} × {self.quantity}'

    @property
    def total_price(self):
        """Вартість позиції = ціна × кількість."""
        return self.price * self.quantity
