FROM python:3

WORKDIR /usr/src/app

RUN mkdir run
RUN mkdir logs/
RUN mkdir bin

RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean
# most of these are for lxml which needs a bunch of dependancies installed
RUN apt-get install -y \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt-dev \
    libjpeg-dev \
    libfreetype6-dev \
    zlib1g-dev \
    net-tools \
    git-all \
    supervisor \
    vim

COPY docker_scripts/vogon-gunicorn.sh bin/
COPY docker_scripts/vogon-supervisord.conf /etc/supervisor/conf.d/
COPY docker_scripts/vogon-backend-startup.sh bin/
RUN ["chmod", "+x", "/usr/src/app/bin/vogon-backend-startup.sh"]
RUN ["chmod", "+x", "/usr/src/app/bin/vogon-gunicorn.sh"]

# TODO: This should be changed to master once we are done testing

RUN git clone -b develop https://github.com/diging/vogon-web.git
WORKDIR /usr/src/app/vogon-web
RUN pip install -r requirements.txt

COPY .env_secrets .
CMD source .env_secrets

ENTRYPOINT ["../bin/vogon-backend-startup.sh"]
