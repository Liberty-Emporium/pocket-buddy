web: mkdir -p ${MEDIA_ROOT:-/data/media} && gunicorn config.wsgi --log-file - --bind 0.0.0.0:${PORT:-8000}
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
