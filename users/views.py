"""
Views приложения 'users'.
Регистрация, вход, выход, профиль и панель менеджера.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta

from .forms import CustomUserCreationForm, CustomUserLoginForm, ProfileEditForm


def _is_manager(user):
    """Проверка: пользователь является менеджером или администратором."""
    return user.is_authenticated and (user.is_staff or user.role in ('manager', 'admin'))


def register_view(request):
    """Регистрация нового пользователя (клиента)."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Ласкаво просимо, {user.first_name}!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """Вход в систему."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'З поверненням, {user.first_name or user.username}!')
            # Перенаправляем на страницу, с которой пришёл пользователь
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        form = CustomUserLoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """Выход из системы."""
    logout(request)
    messages.info(request, 'Ви вийшли з системи.')
    return redirect('home')


@login_required
def profile_view(request):
    """Личный кабинет пользователя с историей заказов."""
    orders = request.user.orders.all().prefetch_related('items__product')
    return render(request, 'users/profile.html', {'orders': orders})


@login_required
def profile_edit_view(request):
    """Редактирование данных профиля пользователя."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль успішно оновлено.')
            return redirect('users:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'users/profile_edit.html', {'form': form})


@user_passes_test(_is_manager, login_url='/users/login/')
def manager_dashboard(request):
    """
    Панель менеджера — ключевая страница демонстрации автоматизации.

    Отображает:
    - Сводные показатели за всё время и за последние 30 дней
    - Статистику заказов по статусам
    - Товары с критически низким остатком (нужна закупка)
    - Последние 10 заказов
    """
    from orders.models import Order
    from warehouse.models import Stock

    # Период для сравнения — последние 30 дней
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # ── Общая статистика ──
    total_orders = Order.objects.count()
    orders_30d   = Order.objects.filter(created_at__gte=thirty_days_ago).count()

    # Выручка считается только по доставленным заказам
    revenue_total = Order.objects.filter(
        status=Order.Status.DELIVERED
    ).aggregate(
        total=Sum(F('items__price') * F('items__quantity'))
    )['total'] or 0

    revenue_30d = Order.objects.filter(
        status=Order.Status.DELIVERED,
        created_at__gte=thirty_days_ago,
    ).aggregate(
        total=Sum(F('items__price') * F('items__quantity'))
    )['total'] or 0

    # ── Заказы по статусам (для диаграммы и таблицы) ──
    orders_by_status = Order.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    status_labels = dict(Order.Status.choices)
    orders_status_data = [
        {
            'status': item['status'],
            'label': status_labels.get(item['status'], item['status']),
            'count': item['count'],
        }
        for item in orders_by_status
    ]

    # ── Товары с низким остатком (≤ 5 штук) — нужна закупка ──
    low_stock = Stock.objects.filter(
        quantity__lte=5
    ).select_related('product__category', 'product__brand').order_by('quantity')

    # ── Последние 10 заказов ──
    recent_orders = Order.objects.select_related('user').prefetch_related(
        'items'
    ).order_by('-created_at')[:10]

    context = {
        'total_orders':       total_orders,
        'orders_30d':         orders_30d,
        'revenue_total':      revenue_total,
        'revenue_30d':        revenue_30d,
        'orders_status_data': orders_status_data,
        'low_stock':          low_stock,
        'recent_orders':      recent_orders,
    }
    return render(request, 'users/manager_dashboard.html', context)
