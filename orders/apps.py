"""
Конфігурація додатку 'orders'.
"""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    verbose_name = 'Замовлення'

    def ready(self):
        """
        Імпортуємо сигнали при запуску додатку.
        Сигнали відповідають за автоматичне списання товару зі складу
        при оформленні замовлення та збереження кошика користувача.
        """
        import orders.signals      # noqa: F401
        import orders.cart_signals  # noqa: F401
