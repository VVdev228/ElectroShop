"""
Модуль моделей додатку 'users'.
Містить кастомну модель користувача з підтримкою ролей:
Клієнт, Менеджер, Адміністратор.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Кастомна модель користувача.
    Розширює стандартну модель Django (AbstractUser), додаючи:
    - role: роль користувача в системі (Клієнт / Менеджер / Адміністратор)
    - phone: номер телефону для зв'язку
    - address: адреса доставки

    Ролі використовуються для розмежування доступу:
    - Клієнт — може переглядати каталог і оформлювати замовлення
    - Менеджер — працює з Django Admin, фіксує прихід товару, керує замовленнями
    - Адміністратор — повний доступ до всіх функцій системи
    """

    class Role(models.TextChoices):
        """Перелік ролей користувачів у системі."""
        CLIENT = 'client', 'Клієнт'
        MANAGER = 'manager', 'Менеджер'
        ADMIN = 'admin', 'Адміністратор'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT,
        verbose_name='Роль',
        help_text='Роль користувача визначає рівень доступу в системі',
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон',
        help_text='Контактний номер телефону',
    )

    address = models.TextField(
        blank=True,
        verbose_name='Адреса доставки',
        help_text='Адреса для доставки замовлень',
    )

    saved_cart = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Збережений кошик',
        help_text='Кошик зберігається автоматично при виході з системи',
    )

    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_client(self):
        """Перевірка: чи є користувач клієнтом."""
        return self.role == self.Role.CLIENT

    @property
    def is_manager(self):
        """Перевірка: чи є користувач менеджером."""
        return self.role == self.Role.MANAGER

    @property
    def is_admin_role(self):
        """Перевірка: чи є користувач адміністратором (за роллю)."""
        return self.role == self.Role.ADMIN
