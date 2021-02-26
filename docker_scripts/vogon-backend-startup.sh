#!/bin/bash
source /usr/src/app/host/env_secrets
service redis-server start
service supervisor start
cd /usr/src/app/host
pip install -r requirements.txt
python manage.py createcachetable
python manage.py migrate

if python manage.py test
then
    echo "runs"
else
    return exit 1
fi
tail -f /dev/null

if python manage.py test; then
else return exit 1 fi
