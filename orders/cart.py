"""
Модуль кошика покупок на базі сесій Django.

Кошик зберігається у сесії користувача (request.session) у вигляді словника:
{
    "cart": {
        "product_id": {
            "quantity": 2,
            "price": "75000.00"
        },
        ...
    }
}

Переваги підходу на сесіях:
- Не вимагає авторизації — працює для всіх відвідувачів
- Не створює зайвих записів у БД
- Автоматично очищається після завершення сесії
- Простота реалізації та тестування
"""

from decimal import Decimal

from django.conf import settings

from catalog.models import Product


# Ключ для зберігання кошика в сесії
CART_SESSION_KEY = 'cart'


class Cart:
    """
    Клас кошика покупок.

    Використання:
        cart = Cart(request)        # Отримати кошик із сесії
        cart.add(product, qty=1)    # Додати товар
        cart.remove(product)        # Видалити товар
        cart.get_total_price()      # Загальна вартість
        len(cart)                   # Кількість позицій
        for item in cart:           # Ітерація по товарах
    """

    def __init__(self, request):
        """
        Ініціалізація кошика.
        Якщо в сесії немає кошика — створюємо порожній словник.
        """
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if not cart:
            # Створюємо порожній кошик у сесії
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Додати товар до кошика або оновити його кількість.

        Параметри:
        - product: об'єкт Product
        - quantity: кількість одиниць
        - override_quantity: якщо True — замінити кількість,
          якщо False — додати до поточної
        """
        product_id = str(product.pk)

        if product_id not in self.cart:
            # Товар додається вперше — зберігаємо ціну
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
        """Видалити товар із кошика."""
        product_id = str(product.pk)
        if product_id in self.cart:
            del self.cart[product_id]
            self._save()

    def __iter__(self):
        """
        Ітерація по товарах у кошику.
        Для кожного товару завантажуємо об'єкт Product з БД
        та додаємо обчислювані поля (total_price).
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        # Глибока копія, щоб не псувати self.cart Decimal-значеннями
        cart = {k: dict(v) for k, v in self.cart.items()}

        for product in products:
            cart_item = cart[str(product.pk)]
            cart_item['product'] = product
            # Оновлюємо ціну до актуальної — щоб клієнт не платив стару ціну
            # якщо менеджер змінив її після додавання в кошик
            cart_item['price'] = str(product.price)
            self.cart[str(product.pk)]['price'] = str(product.price)

        self._save()

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """Загальна кількість позицій у кошику."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Загальна вартість усіх товарів у кошику."""
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def clear(self):
        """Очистити кошик (після оформлення замовлення)."""
        del self.session[CART_SESSION_KEY]
        self.cart = {}
        self._save()

    def _save(self):
        """
        Позначити сесію як змінену.
        Django зберігає сесію лише якщо її було змінено,
        тому при будь-якій зміні кошика потрібно викликати цей метод.
        """
        self.session.modified = True
