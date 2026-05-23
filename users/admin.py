"""
Налаштування Django Admin для додатку 'users'.
Кастомне відображення моделі CustomUser в адміністративній панелі.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Адміністративний інтерфейс для моделі CustomUser.
    Розширює стандартний UserAdmin, додаючи поля ролі, телефону та адреси.
    """

    # Відображення у списку користувачів
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')

    # Додаємо кастомні поля до форми редагування користувача
    fieldsets = UserAdmin.fieldsets + (
        ('Додаткова інформація', {
            'fields': ('role', 'phone', 'address'),
        }),
    )

    # Додаємо кастомні поля до форми створення користувача
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Додаткова інформація', {
            'fields': ('role', 'phone', 'address'),
        }),
    )
