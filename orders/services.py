"""
Сервисный слой приложения 'orders'.

КЛЮЧЕВОЙ МОДУЛЬ АВТОМАТИЗАЦИИ — создание заказа с транзакционным
списанием товара со склада.

Функция create_order_from_cart() — точка входа для оформления заказа:
1. Создаёт объект Order с контактными данными клиента
2. Для каждого товара в корзине создаёт OrderItem
3. АТОМАРНО списывает товар со склада (Stock.quantity -= quantity)
4. Проверяет достаточность остатка (нельзя заказать больше, чем есть)
5. Очищает корзину после успешного оформления

Вся операция обёрнута в @transaction.atomic — если хотя бы одна
позиция не может быть списана, откатываются ВСЕ изменения.
"""

from django.db import transaction
from django.db.models import F

from warehouse.models import Stock
from .models import Order, OrderItem


class InsufficientStockError(Exception):
    """
    Исключение: недостаточно товара на складе.
    Выбрасывается, когда клиент пытается заказать больше,
    чем доступно на складе.
    """

    def __init__(self, product, requested, available):
        self.product = product
        self.requested = requested
        self.available = available
        super().__init__(
            f'Недостаточно товара "{product.name}" на складе. '
            f'Запрошено: {requested}, доступно: {available}'
        )


@transaction.atomic
def create_order_from_cart(cart, form_data, user=None):
    """
    Создание заказа из корзины с атомарным списанием товара со склада.

    АЛГОРИТМ:
    1. Создаём заказ (Order) с данными из формы
    2. Для каждого товара в корзине:
       a) Проверяем наличие на складе (Stock)
       b) Если товара недостаточно — выбрасываем InsufficientStockError
          и ВСЯ транзакция откатывается
       c) Создаём позицию заказа (OrderItem) с фиксированной ценой
       d) Уменьшаем остаток на складе через F-выражение (атомарно)
    3. Очищаем корзину
    4. Возвращаем созданный заказ

    Декоратор @transaction.atomic гарантирует:
    - Либо заказ создан И товар списан — ОК
    - Либо произошла ошибка — ВСЕ изменения откатываются
    Это принцип ACID (Atomicity) — ключевое свойство для
    автоматизации бизнес-процесса.

    Параметры:
    - cart: объект Cart (корзина из сессии)
    - form_data: очищенные данные из OrderCreateForm (cleaned_data)
    - user: объект CustomUser или None (для незарегистрированных)

    Возвращает:
    - order: созданный объект Order

    Выбрасывает:
    - InsufficientStockError: если товара на складе недостаточно
    """

    # Шаг 1: Создаём заказ
    order = Order.objects.create(
        user=user,
        first_name=form_data['first_name'],
        last_name=form_data['last_name'],
        email=form_data['email'],
        phone=form_data['phone'],
        address=form_data['address'],
        notes=form_data.get('notes', ''),
    )

    # Шаг 2: Обрабатываем каждый товар из корзины
    for item in cart:
        product = item['product']
        quantity = item['quantity']
        price = item['price']

        # Шаг 2a: Проверяем наличие на складе
        # select_for_update() блокирует строку Stock на время транзакции,
        # предотвращая гонку данных (race condition) при параллельных заказах
        try:
            stock = Stock.objects.select_for_update().get(product=product)
        except Stock.DoesNotExist:
            # Если записи Stock нет — значит товар никогда не поступал на склад
            raise InsufficientStockError(product, quantity, 0)

        # Шаг 2b: Проверяем достаточность остатка
        if stock.quantity < quantity:
            raise InsufficientStockError(product, quantity, stock.quantity)

        # Шаг 2c: Создаём позицию заказа с фиксированной ценой
        OrderItem.objects.create(
            order=order,
            product=product,
            price=price,
            quantity=quantity,
        )

        # Шаг 2d: Атомарно уменьшаем остаток на складе
        Stock.objects.filter(pk=stock.pk).update(
            quantity=F('quantity') - quantity
        )

        # Шаг 2e: Если склад обнулился — скрываем товар из каталога
        remaining = stock.quantity - quantity
        if remaining == 0:
            product.__class__.objects.filter(pk=product.pk).update(available=False)

    # Шаг 3: Очищаем корзину
    cart.clear()

    # Шаг 4: Возвращаем созданный заказ
    return order
