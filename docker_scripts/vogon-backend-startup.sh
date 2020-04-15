#!/bin/bash
service redis-server start
service supervisor start
docker cp /diging2/docker/python-apps-docker/vogonPython3/vogon_docker_test/vogon-backend/.env_secrets vogon-compose_vogon_1:/.env_secrets
#python manage.py runserver 0.0.0.0:8000
