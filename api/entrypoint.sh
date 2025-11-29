#!/bin/bash
set -e

if [ "$1" = "gunicorn" ]; then
    python manage.py migrate --noinput
    exec gunicorn ${PROJ_NAME}.wsgi:application --bind [::]:$PORT --timeout 300
else
    # Run any other command
    exec "$@"
fi