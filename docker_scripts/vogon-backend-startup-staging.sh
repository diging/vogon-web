#!/bin/bash
cd /usr/src/app/host
pip install -r requirements

source env_secrets

python manage.py createcachetable
python manage.py migrate

service redis-server start
service supervisor start

tail -f /dev/null
