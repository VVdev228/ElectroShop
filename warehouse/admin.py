"""
Настройка Django Admin для приложения 'warehouse'.

КЛЮЧЕВАЯ ЛОГИКА: при изменении статуса поставки на "Получена" в админке
остатки на складе (Stock) автоматически увеличиваются на количество
товара из каждой позиции поставки.

Эта логика реализована в методе save_model() класса SupplyAdmin.
"""

from django.contrib import admin
from django.utils import timezone
from django.db.models import F
from django.db import transaction

from .models import Supplier, Supply, SupplyItem, Stock


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Административный интерфейс для поставщиков."""

    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'email')
    list_per_page = 25


class SupplyItemInline(admin.TabularInline):
    """
    Inline-форма для позиций поставки.
    Позволяет добавлять товары прямо в форме создания/редактирования поставки.
    """

    model = SupplyItem
    extra = 1  # Одна пустая строка для добавления нового товара
    min_num = 1  # Минимум одна позиция в поставке
    autocomplete_fields = ['product']  # Удобный автокомплит для выбора товара


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для поставок.

    АВТОМАТИЗАЦИЯ СКЛАДСКОГО УЧЁТА:
    При изменении статуса поставки на "Получена" (RECEIVED):
    1. Для каждой позиции поставки (SupplyItem) находим или создаём запись Stock
    2. Увеличиваем остаток на складе на количество из позиции
    3. Используем F-выражения Django для атомарного обновления
       (безопасность при параллельных запросах)
    4. Фиксируем дату получения поставки
    5. Всё оборачивается в транзакцию — либо обновляются все остатки,
       либо ни один (принцип атомарности)
    """

    list_display = (
        '__str__', 'supplier', 'status',
        'total_items_display', 'created_at', 'received_at',
    )
    list_filter = ('status', 'supplier', 'created_at')
    search_fields = ('supplier__name', 'notes')
    readonly_fields = ('created_at', 'received_at')
    inlines = [SupplyItemInline]
    list_per_page = 25

    def total_items_display(self, obj):
        """Показывает общее количество единиц товара в поставке."""
        return obj.total_items
    total_items_display.short_description = 'Всего единиц'

    def save_model(self, request, obj, form, change):
        """
        Переопределяем сохранение поставки для автоматического
        обновления складских остатков.

        ЛОГИКА АВТОМАТИЗАЦИИ:
        Если статус меняется на "Получена" (RECEIVED), выполняем
        атомарное обновление остатков на складе.
        """
        # Проверяем: был ли изменён статус на "Получена"
        # change=True означает что объект редактируется (а не создаётся впервые)
        if change and obj.status == Supply.Status.RECEIVED:
            # Проверяем, что статус действительно изменился
            # (чтобы не обновлять остатки повторно при повторном сохранении)
            old_supply = Supply.objects.get(pk=obj.pk)
            if old_supply.status != Supply.Status.RECEIVED:
                # Статус изменился на "Получена" — обновляем остатки
                obj.received_at = timezone.now()
                super().save_model(request, obj, form, change)
                self._update_stock_on_receive(obj)
                return

        super().save_model(request, obj, form, change)

    @transaction.atomic
    def _update_stock_on_receive(self, supply):
        """
        Атомарное обновление остатков на складе при получении поставки.

        Для каждой позиции в поставке:
        1. Ищем запись Stock для данного товара (или создаём с quantity=0)
        2. Увеличиваем quantity на количество из позиции

        Декоратор @transaction.atomic гарантирует, что либо ВСЕ остатки
        обновятся успешно, либо НИ ОДИН (откат транзакции при ошибке).
        Это критически важно для целостности данных складского учёта.
        """
        for item in supply.items.all():
            # get_or_create — если записи Stock для товара нет, создаём с quantity=0
            stock, created = Stock.objects.get_or_create(
                product=item.product,
                defaults={'quantity': 0},
            )

            # F-выражение обновляет значение на уровне БД (атомарная операция).
            # Это защищает от ошибок при параллельном доступе:
            # если два менеджера одновременно фиксируют приход одного товара,
            # оба обновления корректно сложатся.
            Stock.objects.filter(pk=stock.pk).update(
                quantity=F('quantity') + item.quantity
            )
            # Якщо товар був недоступний — вмикаємо його в каталозі
            item.product.__class__.objects.filter(pk=item.product.pk).update(available=True)


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для просмотра остатков на складе.
    Только для просмотра — остатки обновляются автоматически
    через поставки (Supply) и заказы (Order).
    """

    list_display = ('product', 'quantity', 'stock_status', 'updated_at')
    list_filter = ('quantity',)
    search_fields = ('product__name', 'product__sku')
    readonly_fields = ('product', 'quantity', 'updated_at')
    list_per_page = 25

    def stock_status(self, obj):
        """Визуальный индикатор состояния остатка."""
        if obj.quantity == 0:
            return '🔴 Нет в наличии'
        elif obj.quantity <= 5:
            return '🟡 Мало'
        return '🟢 В наличии'
    stock_status.short_description = 'Статус'

    def has_add_permission(self, request):
        """Запрещаем ручное добавление остатков — они создаются автоматически."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Запрещаем удаление остатков вручную."""
        return False
