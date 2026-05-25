web: python manage.py collectstatic --noinput --upload-unhashed-files && python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
