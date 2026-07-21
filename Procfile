web: mkdir -p ${MEDIA_ROOT:-/data/media} && gunicorn config.wsgi --log-file -
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
