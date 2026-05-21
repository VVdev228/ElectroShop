"""
Unit-тести для корзины и оформления заказа.
Запуск: python manage.py test orders
"""

from decimal import Decimal

from django.test import TestCase, RequestFactory
from django.contrib.sessions.backends.db import SessionStore

from catalog.models import Category, Brand, Product
from warehouse.models import Stock
from orders.cart import Cart
from orders.models import Order, OrderItem
from orders.services import create_order_from_cart, InsufficientStockError


def make_product(name='Test', price='1000.00', sku='TEST-001'):
    cat, _ = Category.objects.get_or_create(name='TestCat', slug='testcat')
    brand, _ = Brand.objects.get_or_create(name='TestBrand', slug='testbrand')
    return Product.objects.create(
        category=cat, brand=brand,
        name=name, slug=name.lower().replace(' ', '-'),
        sku=sku, price=Decimal(price),
    )


def make_stock(product, quantity):
    return Stock.objects.create(product=product, quantity=quantity)


def make_cart(items: dict):
    """items = {product: quantity}"""
    factory = RequestFactory()
    request = factory.get('/')
    session = SessionStore()
    session.create()
    request.session = session
    cart = Cart(request)
    for product, qty in items.items():
        cart.add(product, quantity=qty)
    return cart


class CartTest(TestCase):
    def setUp(self):
        self.product = make_product('iPhone', '38999.00', 'APL-001')

    def test_add_product(self):
        cart = make_cart({self.product: 2})
        self.assertEqual(len(cart), 2)

    def test_total_price(self):
        cart = make_cart({self.product: 3})
        self.assertEqual(cart.get_total_price(), Decimal('38999.00') * 3)

    def test_remove_product(self):
        cart = make_cart({self.product: 1})
        cart.remove(self.product)
        self.assertEqual(len(cart), 0)

    def test_override_quantity(self):
        cart = make_cart({self.product: 5})
        cart.add(self.product, quantity=2, override_quantity=True)
        self.assertEqual(len(cart), 2)

    def test_clear(self):
        cart = make_cart({self.product: 3})
        cart.clear()
        self.assertEqual(len(cart), 0)


class OrderCreationTest(TestCase):
    def setUp(self):
        self.product = make_product('Samsung S24', '29999.00', 'SAM-001')
        self.stock = make_stock(self.product, 10)
        self.form_data = {
            'first_name': 'Іван',
            'last_name': 'Петренко',
            'email': 'ivan@example.com',
            'phone': '+380501234567',
            'address': 'Київ, вул. Хрещатик, 1',
            'notes': '',
        }

    def test_order_created(self):
        cart = make_cart({self.product: 2})
        order = create_order_from_cart(cart, self.form_data)
        self.assertIsInstance(order, Order)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 2)

    def test_stock_decreased(self):
        cart = make_cart({self.product: 3})
        create_order_from_cart(cart, self.form_data)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 7)

    def test_insufficient_stock_raises(self):
        cart = make_cart({self.product: 100})
        with self.assertRaises(InsufficientStockError) as ctx:
            create_order_from_cart(cart, self.form_data)
        self.assertEqual(ctx.exception.available, 10)

    def test_insufficient_stock_no_order_created(self):
        cart = make_cart({self.product: 100})
        try:
            create_order_from_cart(cart, self.form_data)
        except InsufficientStockError:
            pass
        self.assertEqual(Order.objects.count(), 0)

    def test_product_marked_unavailable_when_stock_zero(self):
        cart = make_cart({self.product: 10})
        create_order_from_cart(cart, self.form_data)
        self.product.refresh_from_db()
        self.assertFalse(self.product.available)

    def test_order_cancellation_returns_stock(self):
        cart = make_cart({self.product: 4})
        order = create_order_from_cart(cart, self.form_data)
        order.status = Order.Status.CANCELLED
        order.save()
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 10)

    def test_price_fixed_at_order_time(self):
        cart = make_cart({self.product: 1})
        order = create_order_from_cart(cart, self.form_data)
        item = order.items.first()
        self.assertEqual(item.price, Decimal('29999.00'))
        # Меняем цену товара
        self.product.price = Decimal('99999.00')
        self.product.save()
        # Цена в заказе не должна измениться
        item.refresh_from_db()
        self.assertEqual(item.price, Decimal('29999.00'))


class CartAjaxTest(TestCase):
    def setUp(self):
        self.product = make_product('iPad', '19999.00', 'APL-002')
        self.client.get('/')  # init session

    def test_ajax_update_quantity(self):
        # Спочатку додаємо товар
        self.client.post(
            f'/cart/add/{self.product.pk}/',
            {'quantity': 1, 'override': ''},
        )
        import json
        response = self.client.post(
            f'/orders/cart/update/{self.product.pk}/',
            data=json.dumps({'quantity': 3}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['cart_count'], 3)
