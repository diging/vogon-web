#!/bin/bash
export CELERY_TASK_SERIALIZER=json
export DJANGO_SETTINGS_MODULE='vogon.heroku_settings'

python manage.py migrate
python manage.py loaddata vogonuser.xml
python manage.py loaddata vogonweb-data.xml
