"""
Сервісний шар додатку 'orders'.

КЛЮЧОВИЙ МОДУЛЬ АВТОМАТИЗАЦІЇ — створення замовлення з транзакційним
списанням товару зі складу.

Функція create_order_from_cart() — точка входу для оформлення замовлення:
1. Створює об'єкт Order з контактними даними клієнта
2. Для кожного товару в кошику створює OrderItem
3. АТОМАРНО списує товар зі складу (Stock.quantity -= quantity)
4. Перевіряє достатність залишку (не можна замовити більше, ніж є)
5. Очищає кошик після успішного оформлення

Вся операція обгорнута в @transaction.atomic — якщо хоча б одна
позиція не може бути списана, відкочуються ВСІ зміни.
"""

from django.db import transaction
from django.db.models import F

from warehouse.models import Stock
from .models import Order, OrderItem


class InsufficientStockError(Exception):
    """
    Виняток: недостатньо товару на складі.
    Викидається, коли клієнт намагається замовити більше,
    ніж доступно на складі.
    """

    def __init__(self, product, requested, available):
        self.product = product
        self.requested = requested
        self.available = available
        super().__init__(
            f'Недостатньо товару "{product.name}" на складі. '
            f'Запитано: {requested}, доступно: {available}'
        )


@transaction.atomic
def create_order_from_cart(cart, form_data, user=None):
    """
    Створення замовлення з кошика з атомарним списанням товару зі складу.

    АЛГОРИТМ:
    1. Створюємо замовлення (Order) з даними з форми
    2. Для кожного товару в кошику:
       a) Перевіряємо наявність на складі (Stock)
       b) Якщо товару недостатньо — викидаємо InsufficientStockError
          і ВСЯ транзакція відкочується
       c) Створюємо позицію замовлення (OrderItem) з фіксованою ціною
       d) Зменшуємо залишок на складі через F-вираз (атомарно)
    3. Очищаємо кошик
    4. Повертаємо створене замовлення

    Декоратор @transaction.atomic гарантує:
    - Або замовлення створено І товар списаний — OK
    - Або сталася помилка — ВСІ зміни відкочуються
    Це принцип ACID (Atomicity) — ключова властивість для
    автоматизації бізнес-процесу.

    Параметри:
    - cart: об'єкт Cart (кошик із сесії)
    - form_data: очищені дані з OrderCreateForm (cleaned_data)
    - user: об'єкт CustomUser або None (для незареєстрованих)

    Повертає:
    - order: створений об'єкт Order

    Викидає:
    - InsufficientStockError: якщо товару на складі недостатньо
    """

    # Крок 1: Створюємо замовлення
    order = Order.objects.create(
        user=user,
        first_name=form_data['first_name'],
        last_name=form_data['last_name'],
        email=form_data['email'],
        phone=form_data['phone'],
        address=form_data['address'],
        notes=form_data.get('notes', ''),
    )

    # Крок 2: Обробляємо кожен товар із кошика
    for item in cart:
        product = item['product']
        quantity = item['quantity']
        price = item['price']

        # Крок 2a: Перевіряємо наявність на складі.
        # select_for_update() блокує рядок Stock на час транзакції,
        # запобігаючи гонці даних (race condition) при паралельних замовленнях
        try:
            stock = Stock.objects.select_for_update().get(product=product)
        except Stock.DoesNotExist:
            # Якщо запису Stock немає — отже, товар ніколи не надходив на склад
            raise InsufficientStockError(product, quantity, 0)

        # Крок 2b: Перевіряємо достатність залишку
        if stock.quantity < quantity:
            raise InsufficientStockError(product, quantity, stock.quantity)

        # Крок 2c: Створюємо позицію замовлення з фіксованою ціною
        OrderItem.objects.create(
            order=order,
            product=product,
            price=price,
            quantity=quantity,
        )

        # Крок 2d: Атомарно зменшуємо залишок на складі
        Stock.objects.filter(pk=stock.pk).update(
            quantity=F('quantity') - quantity
        )

        # Крок 2e: Якщо склад обнулився — приховуємо товар із каталогу
        remaining = stock.quantity - quantity
        if remaining == 0:
            product.__class__.objects.filter(pk=product.pk).update(available=False)

    # Крок 3: Очищаємо кошик
    cart.clear()

    # Крок 4: Повертаємо створене замовлення
    return order
