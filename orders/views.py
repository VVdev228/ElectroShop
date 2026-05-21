"""
Views приложения 'orders'.
Работа с корзиной и оформление заказа.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages

from catalog.models import Product
from .cart import Cart
from .forms import CartAddProductForm, OrderCreateForm
from .services import create_order_from_cart, InsufficientStockError


@require_POST
def cart_add(request, product_id):
    """
    Добавление товара в корзину (POST-запрос).
    После добавления перенаправляет на страницу корзины.
    """
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        cart.add(
            product=product,
            quantity=cd['quantity'],
            override_quantity=cd['override'],
        )
        messages.success(request, f'Товар «{product.name}» додано до кошика.')

    return redirect('orders:cart_detail')


@require_POST
def cart_remove(request, product_id):
    """Удаление товара из корзины."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f'Товар «{product.name}» видалено з кошика.')
    return redirect('orders:cart_detail')


@require_POST
def cart_update_ajax(request, product_id):
    """AJAX: оновлення кількості товару в кошику. Повертає JSON."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Невірна кількість'}, status=400)

    if quantity < 1:
        cart.remove(product)
    else:
        cart.add(product, quantity=quantity, override_quantity=True)

    item_total = None
    for item in cart:
        if item['product'].pk == product.pk:
            item_total = str(item['total_price'])
            break

    return JsonResponse({
        'ok': True,
        'item_total': item_total,
        'cart_total': str(cart.get_total_price()),
        'cart_count': len(cart),
    })


def cart_detail(request):
    """Страница корзины — список товаров, количество, итого."""
    cart = Cart(request)
    # Для каждого товара в корзине создаём форму обновления количества
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(
            initial={'quantity': item['quantity'], 'override': True}
        )
    context = {'cart': cart}
    return render(request, 'orders/cart.html', context)


def checkout(request):
    """
    Оформление заказа.
    GET — отображает форму с контактными данными.
    POST — создаёт заказ с транзакционным списанием со склада.
    """
    cart = Cart(request)

    # Нельзя оформить пустую корзину
    if len(cart) == 0:
        messages.warning(request, 'Ваш кошик порожній.')
        return redirect('catalog:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                # Вызываем сервисную функцию — атомарное создание заказа
                user = request.user if request.user.is_authenticated else None
                order = create_order_from_cart(cart, form.cleaned_data, user)
                messages.success(request, f'Замовлення #{order.pk} успішно оформлено!')
                return redirect('orders:order_success', order_id=order.pk)

            except InsufficientStockError as e:
                # Товара на складе недостаточно — показываем ошибку
                messages.error(
                    request,
                    f'На жаль, товару «{e.product.name}» недостатньо '
                    f'на складі. Доступно: {e.available} шт.'
                )
    else:
        # Предзаполняем форму данными авторизованного пользователя
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'phone': getattr(request.user, 'phone', ''),
                'address': getattr(request.user, 'address', ''),
            }
        form = OrderCreateForm(initial=initial)

    context = {'cart': cart, 'form': form}
    return render(request, 'orders/checkout.html', context)


def order_success(request, order_id):
    """Страница успешного оформления заказа."""
    context = {'order_id': order_id}
    return render(request, 'orders/order_success.html', context)
