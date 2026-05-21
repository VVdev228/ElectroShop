"""
Сигнали для зберігання та відновлення кошика при вході/виході.

При виході: session cart → user.saved_cart (БД)
При вході:  user.saved_cart + session cart → session cart (merge)
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .cart import CART_SESSION_KEY


@receiver(user_logged_out)
def save_cart_on_logout(sender, request, user, **kwargs):
    """Зберігаємо поточний кошик сесії у профілі користувача."""
    if user is None:
        return
    session_cart = request.session.get(CART_SESSION_KEY, {})
    if session_cart:
        user.saved_cart = session_cart
        user.save(update_fields=['saved_cart'])


@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    """
    Зливаємо збережений кошик (з БД) із поточним анонімним кошиком.
    Якщо товар є в обох — підсумовуємо кількість.
    """
    saved_cart = user.saved_cart or {}
    if not saved_cart:
        return

    session_cart = request.session.get(CART_SESSION_KEY, {})

    for product_id, item in saved_cart.items():
        if product_id in session_cart:
            session_cart[product_id]['quantity'] += item['quantity']
        else:
            session_cart[product_id] = item

    request.session[CART_SESSION_KEY] = session_cart
    request.session.modified = True

    user.saved_cart = {}
    user.save(update_fields=['saved_cart'])
