"""
Главный URL-конфигуратор проекта ElectroShop.
Подключает URL всех приложений.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from catalog.views import product_list

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', product_list, name='home'),             # Главная = каталог
    path('catalog/', include('catalog.urls')),         # Каталог товаров
    path('orders/', include('orders.urls')),           # Заказы и корзина
    path('users/', include('users.urls')),             # Авторизация
]

# В режиме разработки Django раздаёт медиафайлы (изображения товаров)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
