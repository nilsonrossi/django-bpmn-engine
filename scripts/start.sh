#!/bin/bash
set -e
# python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
python manage.py seed --create-superuser

if [[ ${DJANGO_BIND_ADDRESS+x} ]] && [[ ${DJANGO_BIND_PORT+x} ]];
then
    echo "OK! Using custom ADRESSS $DJANGO_BIND_ADDRESS and PORT $DJANGO_BIND_PORT to set Django runserver command"
    # python manage.py runserver ${DJANGO_BIND_ADDRESS}:${DJANGO_BIND_PORT}
    pip install debugpy -t /tmp && python /tmp/debugpy --wait-for-client --listen 0.0.0.0:5678 manage.py runserver ${DJANGO_BIND_ADDRESS}:${DJANGO_BIND_PORT}
else
    echo "Using 0.0.0.0:8000 as parameter for Django runserver command"
    python manage.py runserver 0.0.0.0:8000
fi
