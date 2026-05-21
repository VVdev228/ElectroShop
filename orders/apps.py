"""
Конфигурация приложения 'orders'.
"""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    verbose_name = 'Заказы'

    def ready(self):
        """
        Импортируем сигналы при запуске приложения.
        Сигналы будут созданы на Шаге 5 для автоматического
        списания товара со склада при оформлении заказа.
        """
        import orders.signals  # noqa: F401
