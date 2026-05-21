"""
Настройка Django Admin для приложения 'users'.
Кастомное отображение модели CustomUser в административной панели.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Административный интерфейс для модели CustomUser.
    Расширяет стандартный UserAdmin, добавляя поля роли, телефона и адреса.
    """

    # Отображение в списке пользователей
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')

    # Добавляем кастомные поля в форму редактирования пользователя
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'phone', 'address'),
        }),
    )

    # Добавляем кастомные поля в форму создания пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'phone', 'address'),
        }),
    )
