"""
Сигналы приложения 'orders'.

АВТОМАТИЗАЦИЯ: возврат товара на склад при отмене заказа.

Когда менеджер меняет статус заказа на "Скасовано" (CANCELLED),
сигнал pre_save перехватывает это изменение и автоматически
возвращает все товары из заказа обратно на склад.
"""

from django.db.models import F
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import transaction

from .models import Order
from warehouse.models import Stock


@receiver(pre_save, sender=Order)
def handle_order_cancellation(sender, instance, **kwargs):
    """Сигнал: обработка отмены/восстановления заказа."""
    if not instance.pk:
        return

    try:
        old_order = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    old_status = old_order.status
    new_status = instance.status

    if old_status == new_status:
        return

    if new_status == Order.Status.CANCELLED and old_status != Order.Status.CANCELLED:
        _return_items_to_stock(instance)

    elif old_status == Order.Status.CANCELLED and new_status != Order.Status.CANCELLED:
        _deduct_items_from_stock(instance)


@transaction.atomic
def _return_items_to_stock(order):
    """Возврат товаров на склад при отмене заказа."""
    for item in order.items.select_related('product').all():
        Stock.objects.filter(product=item.product).update(
            quantity=F('quantity') + item.quantity
        )
        # Товар знову доступний — вмикаємо видимість у каталозі
        item.product.__class__.objects.filter(pk=item.product.pk).update(available=True)


@transaction.atomic
def _deduct_items_from_stock(order):
    """
    Повторне списання при відновленні заказу зі скасованого.
    Перевіряємо наявність залишку перед кожним списанням.
    """
    from orders.services import InsufficientStockError

    for item in order.items.select_related('product').all():
        stock = Stock.objects.select_for_update().filter(product=item.product).first()
        if stock is None or stock.quantity < item.quantity:
            available = stock.quantity if stock else 0
            raise InsufficientStockError(item.product, item.quantity, available)

        Stock.objects.filter(pk=stock.pk).update(
            quantity=F('quantity') - item.quantity
        )
        # Якщо склад вичерпався — ховаємо товар з каталогу
        stock.refresh_from_db()
        if stock.quantity == 0:
            item.product.__class__.objects.filter(pk=item.product.pk).update(available=False)
