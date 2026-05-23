"""
Налаштування Django Admin для додатку 'warehouse'.

КЛЮЧОВА ЛОГІКА: при зміні статусу поставки на "Отримана" в адмінці
залишки на складі (Stock) автоматично збільшуються на кількість
товару з кожної позиції поставки.

Ця логіка реалізована у методі save_model() класу SupplyAdmin.
"""

from django.contrib import admin
from django.utils import timezone
from django.db.models import F
from django.db import transaction

from .models import Supplier, Supply, SupplyItem, Stock


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Адміністративний інтерфейс для постачальників."""

    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'email')
    list_per_page = 25


class SupplyItemInline(admin.TabularInline):
    """
    Inline-форма для позицій поставки.
    Дозволяє додавати товари прямо у формі створення/редагування поставки.
    """

    model = SupplyItem
    extra = 1  # Один порожній рядок для додавання нового товару
    min_num = 1  # Мінімум одна позиція в поставці
    autocomplete_fields = ['product']  # Зручний автокомпліт для вибору товару


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    """
    Адміністративний інтерфейс для поставок.

    АВТОМАТИЗАЦІЯ СКЛАДСЬКОГО ОБЛІКУ:
    При зміні статусу поставки на "Отримана" (RECEIVED):
    1. Для кожної позиції поставки (SupplyItem) знаходимо або створюємо запис Stock
    2. Збільшуємо залишок на складі на кількість із позиції
    3. Використовуємо F-вирази Django для атомарного оновлення
       (безпека при паралельних запитах)
    4. Фіксуємо дату отримання поставки
    5. Усе обгортається в транзакцію — або оновлюються всі залишки,
       або жоден (принцип атомарності)
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
        """Показує загальну кількість одиниць товару в поставці."""
        return obj.total_items
    total_items_display.short_description = 'Усього одиниць'

    def save_model(self, request, obj, form, change):
        """
        Перевизначаємо збереження поставки для автоматичного
        оновлення складських залишків.

        ЛОГІКА АВТОМАТИЗАЦІЇ:
        Якщо статус змінюється на "Отримана" (RECEIVED), виконуємо
        атомарне оновлення залишків на складі.
        """
        # Перевіряємо: чи був змінений статус на "Отримана".
        # change=True означає, що об'єкт редагується (а не створюється вперше)
        if change and obj.status == Supply.Status.RECEIVED:
            # Перевіряємо, чи статус справді змінився
            # (щоб не оновлювати залишки повторно при повторному збереженні)
            old_supply = Supply.objects.get(pk=obj.pk)
            if old_supply.status != Supply.Status.RECEIVED:
                # Статус змінився на "Отримана" — оновлюємо залишки
                obj.received_at = timezone.now()
                super().save_model(request, obj, form, change)
                self._update_stock_on_receive(obj)
                return

        super().save_model(request, obj, form, change)

    @transaction.atomic
    def _update_stock_on_receive(self, supply):
        """
        Атомарне оновлення залишків на складі при отриманні поставки.

        Для кожної позиції в поставці:
        1. Шукаємо запис Stock для даного товару (або створюємо з quantity=0)
        2. Збільшуємо quantity на кількість із позиції

        Декоратор @transaction.atomic гарантує, що або ВСІ залишки
        оновляться успішно, або ЖОДЕН (відкат транзакції при помилці).
        Це критично важливо для цілісності даних складського обліку.
        """
        for item in supply.items.all():
            # get_or_create — якщо запису Stock для товару немає, створюємо з quantity=0
            stock, created = Stock.objects.get_or_create(
                product=item.product,
                defaults={'quantity': 0},
            )

            # F-вираз оновлює значення на рівні БД (атомарна операція).
            # Це захищає від помилок при паралельному доступі:
            # якщо два менеджери одночасно фіксують прихід одного товару,
            # обидва оновлення коректно складуться.
            Stock.objects.filter(pk=stock.pk).update(
                quantity=F('quantity') + item.quantity
            )
            # Якщо товар був недоступний — вмикаємо його в каталозі
            item.product.__class__.objects.filter(pk=item.product.pk).update(available=True)


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    """
    Адміністративний інтерфейс для перегляду залишків на складі.
    Лише для перегляду — залишки оновлюються автоматично
    через поставки (Supply) і замовлення (Order).
    """

    list_display = ('product', 'quantity', 'stock_status', 'updated_at')
    list_filter = ('quantity',)
    search_fields = ('product__name', 'product__sku')
    readonly_fields = ('product', 'quantity', 'updated_at')
    list_per_page = 25

    def stock_status(self, obj):
        """Візуальний індикатор стану залишку."""
        if obj.quantity == 0:
            return '🔴 Немає в наявності'
        elif obj.quantity <= 5:
            return '🟡 Мало'
        return '🟢 В наявності'
    stock_status.short_description = 'Статус'

    def has_add_permission(self, request):
        """Забороняємо ручне додавання залишків — вони створюються автоматично."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Забороняємо видалення залишків вручну."""
        return False
