"""
Команда для наповнення бази даних демонстраційними даними.

Запуск:
    python manage.py populate_db

Очистити і заново:
    python manage.py populate_db --clear
"""

import io
import random
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.db import transaction

from PIL import Image, ImageDraw, ImageFont

from catalog.models import Category, Brand, Product
from warehouse.models import Supplier, Supply, SupplyItem, Stock


def make_image(width, height, bg_color, lines, font_size=28):
    """Генерує PNG-зображення з кольоровим фоном і текстом."""
    img = Image.new('RGB', (width, height), color=bg_color)

    # Легкий градієнт зверху
    overlay = Image.new('RGB', (width, height), color='white')
    for y in range(height):
        alpha = int(30 * (1 - y / height))
        for x in range(width):
            r1, g1, b1 = img.getpixel((x, y))
            r2, g2, b2 = overlay.getpixel((x, y))
            img.putpixel((x, y), (
                r1 + (r2 - r1) * alpha // 255,
                g1 + (g2 - g1) * alpha // 255,
                b1 + (b2 - b1) * alpha // 255,
            ))

    draw = ImageDraw.Draw(img)
    draw.rectangle([8, 8, width - 9, height - 9], outline='white', width=2)

    try:
        font_big   = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', font_size - 8)
    except Exception:
        font_big = font_small = ImageFont.load_default()

    total_h = len(lines) * (font_size + 8)
    y_start = (height - total_h) // 2

    for i, (text, big) in enumerate(lines):
        font = font_big if big else font_small
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        y = y_start + i * (font_size + 8)
        draw.text((x + 2, y + 2), text, fill=(0, 0, 0, 80), font=font)
        draw.text((x, y), text, fill='white', font=font)

    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    buf.seek(0)
    return buf.read()


CATEGORIES = [
    {'name': 'Смартфони',  'slug': 'smartfony',   'description': 'Мобільні телефони провідних світових виробників.', 'color': (30, 64, 175),  'icon': 'Смартфони'},
    {'name': 'Ноутбуки',   'slug': 'noutbuki',    'description': 'Ноутбуки для роботи, навчання та розваг.',         'color': (5, 102, 141),  'icon': 'Ноутбуки'},
    {'name': 'Планшети',   'slug': 'planshety',   'description': 'Планшетні комп\'ютери на Android та iPadOS.',       'color': (6, 95, 70),    'icon': 'Планшети'},
    {'name': 'Навушники',  'slug': 'navushniki',  'description': 'Дротові та бездротові навушники.',                 'color': (88, 28, 135),  'icon': 'Навушники'},
    {'name': 'Аксесуари',  'slug': 'aksesuary',   'description': 'Розумні годинники, зарядні пристрої та інше.',     'color': (146, 64, 14),  'icon': 'Аксесуари'},
]

BRANDS = [
    {'name': 'Apple',   'slug': 'apple',   'color': (80, 80, 80)},
    {'name': 'Samsung', 'slug': 'samsung', 'color': (0, 56, 168)},
    {'name': 'Xiaomi',  'slug': 'xiaomi',  'color': (200, 80, 0)},
    {'name': 'ASUS',    'slug': 'asus',    'color': (0, 130, 90)},
    {'name': 'Sony',    'slug': 'sony',    'color': (40, 40, 40)},
]

PRODUCTS = [
    # ── Смартфони ──
    {
        'category': 'Смартфони', 'brand': 'Apple',
        'sku': 'APL-IP15-256', 'name': 'Apple iPhone 15 256GB',
        'price': 38999,
        'description': (
            'Apple iPhone 15 — флагманський смартфон з чіпом A16 Bionic та динамічним островом. '
            'Основна камера 48 МП, дисплей Super Retina XDR 6,1", захист IP68. '
            'Підтримка USB-C, швидке заряджання 20 Вт.'
        ),
        'color': (30, 64, 175),
    },
    {
        'category': 'Смартфони', 'brand': 'Samsung',
        'sku': 'SAM-S24-128', 'name': 'Samsung Galaxy S24 128GB',
        'price': 31999,
        'description': (
            'Samsung Galaxy S24 на платформі Snapdragon 8 Gen 3. '
            'AMOLED-дисплей 6,2" 120 Гц, потрійна камера 50+10+12 МП. '
            'Функції Galaxy AI для обробки фото і тексту. Захист IP68.'
        ),
        'color': (0, 56, 168),
    },
    {
        'category': 'Смартфони', 'brand': 'Xiaomi',
        'sku': 'XMI-14-256', 'name': 'Xiaomi 14 256GB',
        'price': 25999,
        'description': (
            'Xiaomi 14 з процесором Snapdragon 8 Gen 3 та камерою Leica. '
            'AMOLED 6,36" 120 Гц, потрійна камера 50+50+50 МП. '
            'Швидке заряджання 90 Вт, бездротове 50 Вт.'
        ),
        'color': (180, 60, 0),
    },
    {
        'category': 'Смартфони', 'brand': 'Samsung',
        'sku': 'SAM-A55-256', 'name': 'Samsung Galaxy A55 256GB',
        'price': 16999,
        'description': (
            'Samsung Galaxy A55 — смартфон середнього класу з AMOLED 6,6" 120 Гц. '
            'Потрійна камера 50+12+5 МП, захист IP67. '
            'Акумулятор 5000 мАг, швидке заряджання 25 Вт.'
        ),
        'color': (10, 80, 160),
    },

    # ── Ноутбуки ──
    {
        'category': 'Ноутбуки', 'brand': 'Apple',
        'sku': 'APL-MBA-M2-8', 'name': 'Apple MacBook Air 13" M2 8/256GB',
        'price': 46999,
        'description': (
            'MacBook Air на чіпі Apple M2 — ультратонкий ноутбук без вентилятора. '
            'Дисплей Liquid Retina 13,6", 8 ГБ оперативної пам\'яті, 256 ГБ SSD. '
            'До 18 годин автономної роботи. Важить 1,24 кг.'
        ),
        'color': (50, 50, 50),
    },
    {
        'category': 'Ноутбуки', 'brand': 'ASUS',
        'sku': 'ASUS-VBK-i5', 'name': 'ASUS VivoBook 15 i5-1335U',
        'price': 23999,
        'description': (
            'ASUS VivoBook 15 — універсальний ноутбук для роботи та навчання. '
            'Intel Core i5-1335U, 16 ГБ DDR4, 512 ГБ SSD. '
            'Дисплей IPS 15,6" Full HD, вбудована графіка Intel Iris Xe.'
        ),
        'color': (0, 120, 80),
    },
    {
        'category': 'Ноутбуки', 'brand': 'Xiaomi',
        'sku': 'XMI-NBK-16', 'name': 'Xiaomi Mi Notebook Pro 16" i7',
        'price': 34999,
        'description': (
            'Xiaomi Mi Notebook Pro 16 з процесором Intel Core i7-12700H. '
            'OLED-дисплей 16" 4K, 16 ГБ LPDDR5, 512 ГБ NVMe SSD. '
            'GeForce RTX 3050 4 ГБ, вага 1,8 кг.'
        ),
        'color': (160, 60, 0),
    },
    {
        'category': 'Ноутбуки', 'brand': 'ASUS',
        'sku': 'ASUS-ROG-R9', 'name': 'ASUS ROG Strix G16 Ryzen 9',
        'price': 59999,
        'description': (
            'Ігровий ноутбук ASUS ROG Strix G16 на AMD Ryzen 9 7945HX. '
            'IPS 16" 240 Гц QHD, NVIDIA RTX 4070 8 ГБ, 32 ГБ DDR5, 1 ТБ SSD. '
            'Розвинена система охолодження ROG Intelligent Cooling.'
        ),
        'color': (60, 0, 100),
    },

    # ── Планшети ──
    {
        'category': 'Планшети', 'brand': 'Apple',
        'sku': 'APL-IPA-M2-64', 'name': 'Apple iPad Air 11" M2 64GB Wi-Fi',
        'price': 33999,
        'description': (
            'iPad Air на чіпі M2 — потужний і тонкий планшет для творчості. '
            'Liquid Retina 11" True Tone P3, підтримка Apple Pencil Pro. '
            'Touch ID, камера 12 МП, USB-C, до 10 годин роботи.'
        ),
        'color': (5, 90, 60),
    },
    {
        'category': 'Планшети', 'brand': 'Samsung',
        'sku': 'SAM-GTS9-256', 'name': 'Samsung Galaxy Tab S9 256GB Wi-Fi',
        'price': 29999,
        'description': (
            'Samsung Galaxy Tab S9 — флагманський Android-планшет. '
            'AMOLED 11" 120 Гц, Snapdragon 8 Gen 2, 8 ГБ RAM. '
            'S Pen у комплекті, захист IP68, DeX-режим для роботи.'
        ),
        'color': (0, 56, 140),
    },
    {
        'category': 'Планшети', 'brand': 'Xiaomi',
        'sku': 'XMI-PAD6-128', 'name': 'Xiaomi Pad 6 128GB',
        'price': 14999,
        'description': (
            'Xiaomi Pad 6 — продуктивний планшет за доступною ціною. '
            'IPS 11" 144 Гц 2,8K, Snapdragon 870, 6 ГБ RAM. '
            'Акумулятор 8840 мАг, швидке заряджання 33 Вт, чотири динаміки.'
        ),
        'color': (160, 60, 0),
    },

    # ── Навушники ──
    {
        'category': 'Навушники', 'brand': 'Apple',
        'sku': 'APL-APP2-MQD83', 'name': 'Apple AirPods Pro 2-го покоління',
        'price': 10999,
        'description': (
            'AirPods Pro 2 з активним шумопоглинанням ANC нового рівня. '
            'Адаптивний звук, режим прозорості, тривимірний звук. '
            'До 6 годин на одному заряді, 30 годин з чохлом MagSafe.'
        ),
        'color': (80, 20, 120),
    },
    {
        'category': 'Навушники', 'brand': 'Sony',
        'sku': 'SNY-WH1000XM5', 'name': 'Sony WH-1000XM5',
        'price': 12999,
        'description': (
            'Sony WH-1000XM5 — найкращі накладні навушники з ANC. '
            '8 мікрофонів, процесор HD Noise Cancelling QN1. '
            'До 30 годин роботи, швидке заряджання 3 хв = 3 години. LDAC, multipoint.'
        ),
        'color': (30, 30, 30),
    },
    {
        'category': 'Навушники', 'brand': 'Samsung',
        'sku': 'SAM-BUDS2-PRO', 'name': 'Samsung Galaxy Buds2 Pro',
        'price': 5499,
        'description': (
            'Samsung Galaxy Buds2 Pro — компактні TWS навушники з ANC. '
            '360° Audio, підтримка Hi-Fi 24 біт. '
            'До 5 годин з ANC, 18 годин з чохлом. IPX7.'
        ),
        'color': (0, 40, 140),
    },
    {
        'category': 'Навушники', 'brand': 'Xiaomi',
        'sku': 'XMI-BUDS4PRO', 'name': 'Xiaomi Buds 4 Pro',
        'price': 3999,
        'description': (
            'Xiaomi Buds 4 Pro з активним шумопоглинанням 48 дБ. '
            'Звук Hi-Res LHDC, адаптивний EQ. '
            'До 9 годин на одному заряді, 38 годин з чохлом. IP55.'
        ),
        'color': (150, 50, 0),
    },

    # ── Аксесуари ──
    {
        'category': 'Аксесуари', 'brand': 'Apple',
        'sku': 'APL-AWS9-45-ALU', 'name': 'Apple Watch Series 9 GPS 45mm',
        'price': 18999,
        'description': (
            'Apple Watch Series 9 з чіпом S9 та жестом подвійного натискання. '
            'Always-On Retina дисплей 45 мм, датчик ЧСС/ЕКГ/SpO2. '
            'Водозахист WR50, до 18 годин роботи, Apple Pay.'
        ),
        'color': (60, 30, 0),
    },
    {
        'category': 'Аксесуари', 'brand': 'Samsung',
        'sku': 'SAM-GW6-44-ALU', 'name': 'Samsung Galaxy Watch 6 Classic 44mm',
        'price': 12999,
        'description': (
            'Samsung Galaxy Watch 6 Classic — стильний смарт-годинник з поворотним безелем. '
            'AMOLED 44 мм, моніторинг сну, ЕКГ, тиск. '
            'Wear OS 4.0, Galaxy AI, до 40 годин роботи. IP68.'
        ),
        'color': (30, 30, 80),
    },
    {
        'category': 'Аксесуари', 'brand': 'Xiaomi',
        'sku': 'XMI-PWB-65W', 'name': 'Xiaomi 65W GaN зарядний пристрій',
        'price': 1299,
        'description': (
            'Компактний зарядний пристрій Xiaomi на GaN-транзисторах. '
            'Потужність 65 Вт, два порти USB-C + USB-A. '
            'Підтримка PD 3.0, QC 4+, заряджає ноутбук і смартфон одночасно.'
        ),
        'color': (120, 50, 0),
    },
    {
        'category': 'Аксесуари', 'brand': 'ASUS',
        'sku': 'ASUS-ROG-ALLY', 'name': 'ASUS ROG Ally портативна консоль',
        'price': 21999,
        'description': (
            'ASUS ROG Ally — Windows-ігрова консоль з AMD Z1 Extreme. '
            'IPS 7" 120 Гц 1080p, 16 ГБ LPDDR5, 512 ГБ PCIe 4.0. '
            'Сумісна зі Steam, Xbox Game Pass, до 2 годин гри.'
        ),
        'color': (80, 0, 60),
    },
]

SUPPLIERS = [
    {
        'name':           'ТОВ «ТехноЛогістик»',
        'contact_person': 'Іванов Сергій Петрович',
        'phone':          '+380 (44) 123-45-67',
        'email':          'ivanov@technologistic.ua',
        'address':        'м. Київ, вул. Складська, 15',
    },
    {
        'name':           'ТОВ «ІмпортТех»',
        'contact_person': 'Петренко Анна Ігорівна',
        'phone':          '+380 (67) 987-65-43',
        'email':          'petrenko@importtech.ua',
        'address':        'м. Харків, пр. Науки, 100',
    },
]


class Command(BaseCommand):
    help = 'Наповнює базу даних демонстраційними товарами з зображеннями'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистити існуючі дані перед наповненням',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Очищую існуючі дані...')
            SupplyItem.objects.all().delete()
            Supply.objects.all().delete()
            Stock.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            Brand.objects.all().delete()
            Supplier.objects.all().delete()

        self.stdout.write('Створюю категорії...')
        categories = self._create_categories()

        self.stdout.write('Створюю бренди...')
        brands = self._create_brands()

        self.stdout.write('Створюю товари...')
        products = self._create_products(categories, brands)

        self.stdout.write('Створюю постачальників та поставки...')
        self._create_supplies(products)

        total = Product.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n Готово! Створено товарів: {total}. Відкрийте http://127.0.0.1:8000/'
        ))

    def _create_categories(self):
        result = {}
        for data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=data['slug'],
                defaults={'name': data['name'], 'description': data['description']},
            )
            if not cat.image:
                img_bytes = make_image(600, 300, data['color'], [(data['icon'], True)], font_size=44)
                cat.image.save(f"category_{data['slug']}.png", ContentFile(img_bytes), save=True)
            result[data['name']] = cat
            self.stdout.write(f'  Категорія «{cat.name}» — {"створена" if created else "вже є"}')
        return result

    def _create_brands(self):
        result = {}
        for data in BRANDS:
            brand, created = Brand.objects.get_or_create(
                slug=data['slug'],
                defaults={'name': data['name']},
            )
            if not brand.logo:
                img_bytes = make_image(400, 200, data['color'], [(data['name'], True)], font_size=48)
                brand.logo.save(f"brand_{data['slug']}.png", ContentFile(img_bytes), save=True)
            result[data['name']] = brand
            self.stdout.write(f'  Бренд «{brand.name}» — {"створено" if created else "вже є"}')
        return result

    def _create_products(self, categories, brands):
        import re
        result = {}
        for data in PRODUCTS:
            category = categories[data['category']]
            brand    = brands[data['brand']]
            slug = re.sub(r'[^a-z0-9-]', '-', data['sku'].lower())
            slug = re.sub(r'-+', '-', slug).strip('-')

            product, created = Product.objects.get_or_create(
                sku=data['sku'],
                defaults={
                    'category':    category,
                    'brand':       brand,
                    'name':        data['name'],
                    'slug':        slug,
                    'description': data['description'],
                    'price':       data['price'],
                    'available':   True,
                },
            )
            if not product.image:
                lines = [
                    (brand.name.upper(), False),
                    (data['name'][:26], True),
                    (f"{data['price']:,} UAH".replace(',', ' '), False),
                ]
                img_bytes = make_image(600, 600, data['color'], lines, font_size=30)
                product.image.save(
                    f"product_{data['sku'].lower()}.png",
                    ContentFile(img_bytes),
                    save=True,
                )
            result[data['sku']] = product
            self.stdout.write(f'  [{data["category"]}] {product.name} — {"створено" if created else "вже є"}')
        return result

    def _create_supplies(self, products):
        for sup_data in SUPPLIERS:
            Supplier.objects.get_or_create(
                name=sup_data['name'],
                defaults={k: v for k, v in sup_data.items() if k != 'name'},
            )

        if Stock.objects.count() == 0:
            from django.utils import timezone
            suppliers = list(Supplier.objects.all())
            supply = Supply.objects.create(
                supplier=suppliers[0],
                status=Supply.Status.RECEIVED,
                received_at=timezone.now(),
                notes='Початковий залишок складу',
            )
            for sku, product in products.items():
                qty = random.randint(5, 25)
                SupplyItem.objects.create(
                    supply=supply,
                    product=product,
                    quantity=qty,
                    purchase_price=product.price * 70 // 100,
                )
                Stock.objects.update_or_create(
                    product=product,
                    defaults={'quantity': qty},
                )
            self.stdout.write(f'  Поставка #{supply.pk} створена, залишки складу заповнено.')
        else:
            self.stdout.write('  Залишки складу вже існують, пропускаю.')
