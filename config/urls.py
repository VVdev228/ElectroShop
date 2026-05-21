"""
Главный URL-конфигуратор проекта ElectroShop.
Подключает URL всех приложений.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from catalog.views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('catalog/', include('catalog.urls')),         # Каталог товаров
    path('orders/', include('orders.urls')),           # Заказы и корзина
    path('users/', include('users.urls')),             # Авторизация
]

# В режиме разработки Django раздаёт медиафайлы (изображения товаров)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
