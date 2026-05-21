"""
Django settings для проекта ElectroShop.
Дипломный проект: Информационная система автоматизации розничной торговли
магазина электроники на базе интернет-магазина.
"""

import os
from pathlib import Path
from decouple import config, Csv

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())


# ──────────────────────────────────────────────
# Приложения
# ──────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Приложения проекта
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
        # Глобальная директория шаблонов (для base.html и общих шаблонов)
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
# База данных — PostgreSQL
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
# Валидация паролей
# ──────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ──────────────────────────────────────────────
# Интернационализация — русский язык
# ──────────────────────────────────────────────

LANGUAGE_CODE = 'uk'
TIME_ZONE = 'Europe/Kyiv'
USE_I18N = True
USE_TZ = True


# ──────────────────────────────────────────────
# Статические файлы (CSS, JavaScript, изображения)
# ──────────────────────────────────────────────

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # Директория для статики в разработке
STATIC_ROOT = BASE_DIR / 'staticfiles'    # Директория для collectstatic


# ──────────────────────────────────────────────
# Медиафайлы (загружаемые пользователями изображения товаров)
# ──────────────────────────────────────────────

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ──────────────────────────────────────────────
# Кастомная модель пользователя
# ──────────────────────────────────────────────

# ВАЖНО: указываем ДО первой миграции, иначе Django не позволит
# переключиться на кастомную модель пользователя
AUTH_USER_MODEL = 'users.CustomUser'


# ──────────────────────────────────────────────
# Настройки авторизации
# ──────────────────────────────────────────────

LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# Автоинкремент по умолчанию
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
