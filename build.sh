#!/usr/bin/env bash
set -euo pipefail

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-tickets.settings.demo}"

python -m pip install -r requirements/demo.txt

python manage.py migrate --settings="$DJANGO_SETTINGS_MODULE" --noinput
python manage.py createsuperuser --username demo --email tickets_demo@demo.com --noinput
python manage.py collectstatic --settings="$DJANGO_SETTINGS_MODULE" --noinput
