from django import template
from django.db.models import Sum, Count, F

from orders.models import Order, OrderItem
from warehouse.models import Stock

register = template.Library()


@register.simple_tag
def dashboard_stats():
    status_counts = dict(
        Order.objects.values_list('status').annotate(n=Count('id'))
    )

    revenue = (
        OrderItem.objects
        .filter(order__status=Order.Status.DELIVERED)
        .aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
    )

    low_stock = (
        Stock.objects
        .filter(quantity__lte=5)
        .select_related('product')
        .order_by('quantity')[:10]
    )

    recent_orders = (
        Order.objects
        .select_related('user')
        .order_by('-created_at')[:5]
    )

    return {
        'total_orders':      Order.objects.count(),
        'new_orders':        status_counts.get(Order.Status.NEW, 0),
        'processing_orders': status_counts.get(Order.Status.PROCESSING, 0),
        'shipped_orders':    status_counts.get(Order.Status.SHIPPED, 0),
        'delivered_orders':  status_counts.get(Order.Status.DELIVERED, 0),
        'cancelled_orders':  status_counts.get(Order.Status.CANCELLED, 0),
        'revenue':           revenue,
        'low_stock':         low_stock,
        'recent_orders':     recent_orders,
    }
