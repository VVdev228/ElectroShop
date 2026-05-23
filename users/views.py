"""
Views додатку 'users'.
Реєстрація, вхід, вихід, профіль та панель менеджера.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import update_session_auth_hash
from .forms import CustomUserCreationForm, CustomUserLoginForm, ProfileEditForm, CustomPasswordChangeForm


def _is_manager(user):
    """Перевірка: користувач є менеджером або адміністратором."""
    return user.is_authenticated and (user.is_staff or user.role in ('manager', 'admin'))


def register_view(request):
    """Реєстрація нового користувача (клієнта)."""
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
    """Вхід до системи."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'З поверненням, {user.first_name or user.username}!')
            # Перенаправляємо на сторінку, з якої прийшов користувач
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        form = CustomUserLoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """Вихід із системи."""
    logout(request)
    messages.info(request, 'Ви вийшли з системи.')
    return redirect('home')


@login_required
def profile_view(request):
    """Особистий кабінет користувача з історією замовлень."""
    orders = request.user.orders.all().prefetch_related('items__product')
    return render(request, 'users/profile.html', {'orders': orders})


@login_required
def profile_edit_view(request):
    """Редагування даних профілю користувача."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль успішно оновлено.')
            return redirect('users:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'users/profile_edit.html', {'form': form})


@login_required
def password_change_view(request):
    """Зміна пароля користувача."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успішно змінено.')
            return redirect('users:profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'users/password_change.html', {'form': form})


@user_passes_test(_is_manager, login_url='/users/login/')
def manager_dashboard(request):
    """
    Панель менеджера — ключова сторінка демонстрації автоматизації.

    Відображає:
    - Зведені показники за весь час і за останні 30 днів
    - Статистику замовлень за статусами
    - Товари з критично низьким залишком (потрібна закупівля)
    - Останні 10 замовлень
    """
    from orders.models import Order
    from warehouse.models import Stock

    # Період для порівняння — останні 30 днів
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # ── Загальна статистика ──
    total_orders = Order.objects.count()
    orders_30d   = Order.objects.filter(created_at__gte=thirty_days_ago).count()

    # Виторг рахується лише за доставленими замовленнями
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

    # ── Замовлення за статусами (для діаграми і таблиці) ──
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

    # ── Товари з низьким залишком (≤ 5 штук) — потрібна закупівля ──
    low_stock = Stock.objects.filter(
        quantity__lte=5
    ).select_related('product__category', 'product__brand').order_by('quantity')

    # ── Останні 10 замовлень ──
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
