# ElectroShop

Інформаційна система автоматизації роздрібної торгівлі магазину електроніки на базі інтернет-магазину.

## Технології

- Python 3.x
- Django 5+
- PostgreSQL
- Pillow

## Встановлення та запуск

### 1. Клонувати репозиторій

```bash
git clone https://github.com/VVdev228/ElectroShop.git
cd ElectroShop
```

### 2. Створити та активувати віртуальне середовище

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Встановити залежності

```bash
pip install -r requirements.txt
```

### 4. Налаштувати змінні середовища

```bash
cp .env.example .env
```

Відкрити `.env` і заповнити значення:

- `SECRET_KEY` — секретний ключ Django (згенерувати: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD` — дані для підключення до PostgreSQL

### 5. Створити базу даних PostgreSQL

```sql
CREATE DATABASE electroshop;
```

### 6. Застосувати міграції

```bash
python manage.py migrate
```

### 7. Створити суперкористувача (адмін)

```bash
python manage.py createsuperuser
```

### 8. Запустити сервер

```bash
python manage.py runserver
```

Сайт буде доступний за адресою: http://127.0.0.1:8000/  
Адмін-панель: http://127.0.0.1:8000/admin/
