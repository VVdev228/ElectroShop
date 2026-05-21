"""
Настройка Django Admin для приложения 'orders'.
"""

import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from django.db.models import Prefetch, Sum, F, ExpressionWrapper, DecimalField

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity', 'total_price_display')

    def total_price_display(self, obj):
        if obj.pk:
            return format_html('<b>{} ₴</b>', obj.total_price)
        return '—'
    total_price_display.short_description = 'Сума'


def export_orders_csv(modeladmin, request, queryset):
    """Admin action: export selected orders to CSV."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    response.write('﻿')  # BOM для корректного открытия в Excel

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Ім\'я', 'Прізвище', 'Email', 'Телефон',
        'Адреса', 'Статус', 'Сума (₴)', 'Дата',
    ])
    for order in queryset.prefetch_related('items'):
        writer.writerow([
            order.pk,
            order.first_name,
            order.last_name,
            order.email,
            order.phone,
            order.address,
            order.get_status_display(),
            order.total_cost,
            order.created_at.strftime('%d.%m.%Y %H:%M'),
        ])
    return response

export_orders_csv.short_description = 'Експортувати вибрані замовлення в CSV'


def mark_delivered(modeladmin, request, queryset):
    """Admin action: set selected orders to DELIVERED."""
    queryset.update(status=Order.Status.DELIVERED)

mark_delivered.short_description = 'Позначити як "Доставлено"'


def mark_processing(modeladmin, request, queryset):
    queryset.update(status=Order.Status.PROCESSING)

mark_processing.short_description = 'Позначити як "В обробці"'


STATUS_COLORS = {
    Order.Status.NEW:        ('#1e40af', '#dbeafe'),
    Order.Status.PROCESSING: ('#92400e', '#fef3c7'),
    Order.Status.SHIPPED:    ('#3730a3', '#e0e7ff'),
    Order.Status.DELIVERED:  ('#065f46', '#d1fae5'),
    Order.Status.CANCELLED:  ('#991b1b', '#fee2e2'),
}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id', 'full_name', 'email', 'phone',
        'status_badge', 'status', 'total_cost_display', 'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'user')
    list_editable = ('status',)
    inlines = [OrderItemInline]
    list_per_page = 25
    actions = [export_orders_csv, mark_delivered, mark_processing]
    list_select_related = ('user',)

    fieldsets = (
        ('Клієнт', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone'),
        }),
        ('Доставка', {
            'fields': ('address',),
        }),
        ('Статус і дати', {
            'fields': ('status', 'created_at', 'updated_at', 'notes'),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('product'))
        )

    def order_id(self, obj):
        return f'#{obj.pk}'
    order_id.short_description = 'Замовлення'
    order_id.admin_order_field = 'pk'

    def full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'
    full_name.short_description = 'Клієнт'

    def status_badge(self, obj):
        color, bg = STATUS_COLORS.get(obj.status, ('#374151', '#f3f4f6'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:12px;'
            'font-size:0.78rem;font-weight:600;">{}</span>',
            bg, color, obj.get_status_display(),
        )
    status_badge.short_description = 'Статус'

    def total_cost_display(self, obj):
        # total_cost uses prefetched items — no extra queries
        return format_html('<b>{} ₴</b>', obj.total_cost)
    total_cost_display.short_description = 'Сума'
