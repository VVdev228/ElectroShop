"""
Модели приложения 'orders'.

Заказ (Order) — оформленная клиентом покупка, содержащая одну или
несколько позиций (OrderItem). При создании заказа товар автоматически
списывается со склада (см. orders/signals.py — Шаг 5).
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from catalog.models import Product


class Order(models.Model):
    """
    Заказ клиента.

    Статусы жизненного цикла заказа:
    - NEW (Новый) — клиент оформил заказ, товар списан со склада
    - PROCESSING (В обработке) — менеджер взял заказ в работу
    - SHIPPED (Отправлен) — заказ передан в доставку
    - DELIVERED (Доставлен) — клиент получил заказ
    - CANCELLED (Отменён) — заказ отменён (товар возвращается на склад)
    """

    class Status(models.TextChoices):
        NEW = 'new', 'Новий'
        PROCESSING = 'processing', 'В обробці'
        SHIPPED = 'shipped', 'Відправлено'
        DELIVERED = 'delivered', 'Доставлено'
        CANCELLED = 'cancelled', 'Скасовано'

    # Связь с пользователем (может быть NULL для незарегистрированных покупателей)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Пользователь',
    )

    # Контактные данные для доставки
    first_name = models.CharField(
        max_length=100,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name='Фамилия',
    )
    email = models.EmailField(
        verbose_name='Email',
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='Телефон',
    )
    address = models.TextField(
        verbose_name='Адрес доставки',
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
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Комментарий к заказу',
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.pk} — {self.first_name} {self.last_name}'

    @property
    def total_cost(self):
        """Общая стоимость заказа = сумма стоимостей всех позиций."""
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    """
    Позиция в заказе — конкретный товар, его количество и цена
    на момент оформления заказа.

    ВАЖНО: цена фиксируется в момент оформления заказа (поле price),
    чтобы изменение цены товара в каталоге не влияло на уже
    оформленные заказы.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ',
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
        verbose_name='Цена на момент заказа (₴)',
        help_text='Фиксируется при оформлении, не зависит от текущей цены товара',
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Количество',
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f'{self.product.name} × {self.quantity}'

    @property
    def total_price(self):
        """Стоимость позиции = цена × количество."""
        return self.price * self.quantity
