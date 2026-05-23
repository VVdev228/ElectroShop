"""
Views додатку 'catalog'.
Відображення каталогу товарів та карток товарів.
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


CATEGORY_ICONS = {
    'smartfony':  'bi-phone',
    'noutbuki':   'bi-laptop',
    'planshety':  'bi-tablet',
    'navushniki': 'bi-headphones',
    'aksesuary':  'bi-plug',
}


def home_view(request):
    """Головна сторінка з hero-банером та підбіркою товарів."""
    featured = Product.objects.filter(available=True).select_related('category', 'brand').order_by('-created_at')[:8]
    categories = Category.objects.all()
    categories_with_icons = [(c, CATEGORY_ICONS.get(c.slug, 'bi-grid')) for c in categories]
    return render(request, 'home.html', {
        'featured': featured,
        'categories_with_icons': categories_with_icons,
    })


def product_list(request, category_slug=None):
    """
    Сторінка каталогу — список товарів з пошуком, фільтрацією та пагінацією.

    GET-параметри:
    - q: пошуковий запит (за назвою, артикулом, описом)
    - brand: фільтр за брендом (id)
    - min_price, max_price: діапазон цін
    - sort: сортування (price_asc, price_desc, name, newest)
    - page: номер сторінки
    """
    category = None
    categories_with_brands = _build_categories_with_brands()
    brands = Brand.objects.all()
    products = Product.objects.filter(available=True).select_related('category', 'brand')

    # Фільтр за категорією (через URL-slug)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Пошук за текстом — шукаємо у назві, артикулі та описі
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query)
        )

    # Фільтр за брендом
    brand_id = request.GET.get('brand')
    if brand_id:
        products = products.filter(brand_id=brand_id)

    # Фільтр за ціною
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

    # Сортування
    sort = request.GET.get('sort', 'newest')
    sort_options = {
        'price_asc':  'price',
        'price_desc': '-price',
        'name':       'name',
        'newest':     '-created_at',
    }
    products = products.order_by(sort_options.get(sort, '-created_at'))

    # Пагінація — 9 товарів на сторінку (3×3 сітка)
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'categories_with_brands': categories_with_brands,
        'brands': brands,
        'page_obj': page_obj,
        'products': page_obj,        # для сумісності із шаблоном
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
    Картка товару — детальна інформація про товар.
    Показує наявність на складі та форму додавання до кошика.
    """
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related('images'),
        slug=slug,
        available=True,
    )

    # Отримуємо залишок на складі (якщо запис Stock існує)
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
