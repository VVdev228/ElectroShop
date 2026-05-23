"""
Django settings для проекту ElectroShop.
Дипломний проект: Інформаційна система автоматизації роздрібної торгівлі
магазину електроніки на базі інтернет-магазину.
"""

import os
from pathlib import Path
from decouple import config, Csv

# Базова директорія проекту
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())


# ──────────────────────────────────────────────
# Додатки
# ──────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Додатки проекту
    'users.apps.UsersConfig',
    'catalog.apps.CatalogConfig',
    'warehouse.apps.WarehouseConfig',
    'orders.apps.OrdersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Глобальна директорія шаблонів (для base.html та спільних шаблонів)
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'orders.context_processors.cart_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ──────────────────────────────────────────────
# База даних — PostgreSQL
# ──────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='electroshop'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}


# ──────────────────────────────────────────────
# Валідація паролів
# ──────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ──────────────────────────────────────────────
# Інтернаціоналізація — українська мова
# ──────────────────────────────────────────────

LANGUAGE_CODE = 'uk'
TIME_ZONE = 'Europe/Kyiv'
USE_I18N = True
USE_TZ = True


# ──────────────────────────────────────────────
# Статичні файли (CSS, JavaScript, зображення)
# ──────────────────────────────────────────────

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # Директорія для статики під час розробки
STATIC_ROOT = BASE_DIR / 'staticfiles'    # Директорія для collectstatic


# ──────────────────────────────────────────────
# Медіафайли (завантажені користувачами зображення товарів)
# ──────────────────────────────────────────────

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ──────────────────────────────────────────────
# Кастомна модель користувача
# ──────────────────────────────────────────────

# ВАЖЛИВО: вказуємо ДО першої міграції, інакше Django не дозволить
# перейти на кастомну модель користувача
AUTH_USER_MODEL = 'users.CustomUser'


# ──────────────────────────────────────────────
# Налаштування авторизації
# ──────────────────────────────────────────────

LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# Автоінкремент за замовчуванням
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
