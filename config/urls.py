"""
Головний URL-конфігуратор проекту ElectroShop.
Підключає URL усіх додатків.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from catalog.views import home_view

# Українізація заголовків панелі адміністратора
admin.site.site_header = 'ElectroShop — панель адміністратора'
admin.site.site_title = 'Адміністрування ElectroShop'
admin.site.index_title = 'Керування магазином'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('catalog/', include('catalog.urls')),         # Каталог товарів
    path('orders/', include('orders.urls')),           # Замовлення та кошик
    path('users/', include('users.urls')),             # Авторизація
    path('silk/', include('silk.urls', namespace='silk')), 
]

# У режимі розробки Django роздає медіафайли (зображення товарів)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
