#!/bin/bash
source /usr/src/app/data/env_secrets
service redis-server start
service supervisor start
cd /usr/src/app/vogon-web
python manage.py createcachetable
python manage.py migrate
python manage.py test

if [[ $? -eq 0 ]]; then
   docker stop ${CONTAINER_NAME}
   exit 0 # success
else
   docker stop ${CONTAINER_NAME}
   exit 1 # fail
tail -f /dev/null

if python manage.py test; then
else return exit 1 fi
