"""
Модуль корзины покупок на базе сессий Django.

Корзина хранится в сессии пользователя (request.session) в виде словаря:
{
    "cart": {
        "product_id": {
            "quantity": 2,
            "price": "75000.00"
        },
        ...
    }
}

Преимущества подхода на сессиях:
- Не требует авторизации — работает для всех посетителей
- Не создаёт лишних записей в БД
- Автоматически очищается при истечении сессии
- Простота реализации и тестирования
"""

from decimal import Decimal

from django.conf import settings

from catalog.models import Product


# Ключ для хранения корзины в сессии
CART_SESSION_KEY = 'cart'


class Cart:
    """
    Класс корзины покупок.

    Использование:
        cart = Cart(request)        # Получить корзину из сессии
        cart.add(product, qty=1)    # Добавить товар
        cart.remove(product)        # Удалить товар
        cart.get_total_price()      # Общая стоимость
        len(cart)                   # Количество позиций
        for item in cart:           # Итерация по товарам
    """

    def __init__(self, request):
        """
        Инициализация корзины.
        Если в сессии нет корзины — создаём пустой словарь.
        """
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if not cart:
            # Создаём пустую корзину в сессии
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Добавить товар в корзину или обновить его количество.

        Параметры:
        - product: объект Product
        - quantity: количество единиц
        - override_quantity: если True — заменить количество,
          если False — прибавить к текущему
        """
        product_id = str(product.pk)

        if product_id not in self.cart:
            # Товар добавляется впервые — сохраняем цену
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self._save()

    def remove(self, product):
        """Удалить товар из корзины."""
        product_id = str(product.pk)
        if product_id in self.cart:
            del self.cart[product_id]
            self._save()

    def __iter__(self):
        """
        Итерация по товарам в корзине.
        Для каждого товара загружаем объект Product из БД
        и добавляем вычисляемые поля (total_price).
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        # Глибока копія, щоб не псувати self.cart Decimal-значеннями
        cart = {k: dict(v) for k, v in self.cart.items()}

        for product in products:
            cart[str(product.pk)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """Общее количество позиций в корзине."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Общая стоимость всех товаров в корзине."""
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def clear(self):
        """Очистить корзину (после оформления заказа)."""
        del self.session[CART_SESSION_KEY]
        self.cart = {}
        self._save()

    def _save(self):
        """
        Пометить сессию как изменённую.
        Django сохраняет сессию только если она была изменена,
        поэтому при любом изменении корзины нужно вызывать этот метод.
        """
        self.session.modified = True
