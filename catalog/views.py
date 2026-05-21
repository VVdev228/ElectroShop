"""
Views приложения 'catalog'.
Отображение каталога товаров и карточек товаров.
"""

from collections import defaultdict

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Category, Brand, Product
from orders.forms import CartAddProductForm


def _build_categories_with_brands():
    """Повертає список (category, [brands]) для сайдбару каталогу."""
    cat_brands_map = defaultdict(dict)
    for p in Product.objects.filter(available=True).select_related('category', 'brand'):
        cat_brands_map[p.category_id][p.brand_id] = p.brand
    result = []
    for cat in Category.objects.order_by('name'):
        brands_list = sorted(cat_brands_map.get(cat.id, {}).values(), key=lambda b: b.name)
        result.append((cat, brands_list))
    return result


def product_list(request, category_slug=None):
    """
    Страница каталога — список товаров с поиском, фильтрацией и пагинацией.

    GET-параметры:
    - q: поисковый запрос (по названию, артикулу, описанию)
    - brand: фильтр по бренду (id)
    - min_price, max_price: диапазон цен
    - sort: сортировка (price_asc, price_desc, name, newest)
    - page: номер страницы
    """
    category = None
    categories_with_brands = _build_categories_with_brands()
    brands = Brand.objects.all()
    products = Product.objects.filter(available=True).select_related('category', 'brand')

    # Фильтр по категории (через URL-slug)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Поиск по тексту — ищем в названии, артикуле и описании
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query)
        )

    # Фильтр по бренду
    brand_id = request.GET.get('brand')
    if brand_id:
        products = products.filter(brand_id=brand_id)

    # Фильтр по цене
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Сортировка
    sort = request.GET.get('sort', 'newest')
    sort_options = {
        'price_asc':  'price',
        'price_desc': '-price',
        'name':       'name',
        'newest':     '-created_at',
    }
    products = products.order_by(sort_options.get(sort, '-created_at'))

    # Пагинация — 9 товаров на страницу (3×3 сетка)
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'categories_with_brands': categories_with_brands,
        'brands': brands,
        'page_obj': page_obj,
        'products': page_obj,        # для совместимости с шаблоном
        'query': query,
        'sort': sort,
        'brand_id': brand_id or '',
        'min_price': min_price or '',
        'max_price': max_price or '',
        'total_count': paginator.count,
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail(request, slug):
    """
    Карточка товара — подробная информация о товаре.
    Показывает наличие на складе и форму добавления в корзину.
    """
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related('images'),
        slug=slug,
        available=True,
    )

    # Получаем остаток на складе (если запись Stock существует)
    stock_quantity = 0
    try:
        stock_quantity = product.stock.quantity
    except Exception:
        pass

    cart_form = CartAddProductForm()

    # Збираємо всі зображення: головне + галерея
    gallery = []
    if product.image:
        gallery.append(product.image.url)
    for img in product.images.all():
        gallery.append(img.image.url)

    context = {
        'product': product,
        'stock_quantity': stock_quantity,
        'cart_form': cart_form,
        'gallery': gallery,
    }
    return render(request, 'catalog/product_detail.html', context)
