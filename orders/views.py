"""
Views додатку 'orders'.
Робота з кошиком та оформлення замовлення.
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
    Додавання товару до кошика (POST-запит).
    Після додавання перенаправляє на сторінку кошика.
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
    """Видалення товару з кошика."""
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
    """Сторінка кошика — список товарів, кількість, разом."""
    cart = Cart(request)
    # Для кожного товару в кошику створюємо форму оновлення кількості
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(
            initial={'quantity': item['quantity'], 'override': True}
        )
    context = {'cart': cart}
    return render(request, 'orders/cart.html', context)


def checkout(request):
    """
    Оформлення замовлення.
    GET — відображає форму з контактними даними.
    POST — створює замовлення з транзакційним списанням зі складу.
    """
    cart = Cart(request)

    # Не можна оформити порожній кошик
    if len(cart) == 0:
        messages.warning(request, 'Ваш кошик порожній.')
        return redirect('catalog:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                # Викликаємо сервісну функцію — атомарне створення замовлення
                user = request.user if request.user.is_authenticated else None
                order = create_order_from_cart(cart, form.cleaned_data, user)
                messages.success(request, f'Замовлення #{order.pk} успішно оформлено!')
                return redirect('orders:order_success', order_id=order.pk)

            except InsufficientStockError as e:
                # Товару на складі недостатньо — показуємо помилку
                messages.error(
                    request,
                    f'На жаль, товару «{e.product.name}» недостатньо '
                    f'на складі. Доступно: {e.available} шт.'
                )
    else:
        # Передзаповнюємо форму даними авторизованого користувача
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
    """Сторінка успішного оформлення замовлення."""
    context = {'order_id': order_id}
    return render(request, 'orders/order_success.html', context)
