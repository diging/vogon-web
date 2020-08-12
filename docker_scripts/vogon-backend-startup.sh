#!/bin/bash
source /usr/src/app/data/env_secrets
service redis-server start
service supervisor start
cd /usr/src/app/vogon-web
python manage.py migrate
tail -f /dev/null
