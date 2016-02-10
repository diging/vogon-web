#!/bin/bash     
export CELERY_TASK_SERIALIZER=json
export REDIS_URL=redis://
export DJANGO_SETTINGS_MODULE='vogon.local_settings'

python manage.py migrate
python manage.py loaddata vogonweb-data.xml
