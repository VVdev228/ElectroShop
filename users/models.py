"""
Модуль моделей приложения 'users'.
Содержит кастомную модель пользователя с поддержкой ролей:
Клиент, Менеджер, Администратор.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя.
    Расширяет стандартную модель Django (AbstractUser), добавляя:
    - role: роль пользователя в системе (Клиент / Менеджер / Администратор)
    - phone: номер телефона для связи
    - address: адрес доставки

    Роли используются для разграничения доступа:
    - Клиент — может просматривать каталог и оформлять заказы
    - Менеджер — работает с Django Admin, фиксирует приход товара, управляет заказами
    - Администратор — полный доступ ко всем функциям системы
    """

    class Role(models.TextChoices):
        """Перечисление ролей пользователей в системе."""
        CLIENT = 'client', 'Клієнт'
        MANAGER = 'manager', 'Менеджер'
        ADMIN = 'admin', 'Адміністратор'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT,
        verbose_name='Роль',
        help_text='Роль пользователя определяет уровень доступа в системе',
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон',
        help_text='Контактный номер телефона',
    )

    address = models.TextField(
        blank=True,
        verbose_name='Адрес доставки',
        help_text='Адрес для доставки заказов',
    )

    saved_cart = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Збережений кошик',
        help_text='Кошик зберігається автоматично при виході з системи',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_client(self):
        """Проверка: является ли пользователь клиентом."""
        return self.role == self.Role.CLIENT

    @property
    def is_manager(self):
        """Проверка: является ли пользователь менеджером."""
        return self.role == self.Role.MANAGER

    @property
    def is_admin_role(self):
        """Проверка: является ли пользователь администратором (по роли)."""
        return self.role == self.Role.ADMIN
