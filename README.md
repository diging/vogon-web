# VogonWeb

VogonWeb is a web-based platform for encoding your interpretations of texts.
The annotation interface allows you to tag words or phrases with the concepts to
which you believe they refer, and bring those tags together into relational
statements that you believe are supported by the text. These tags and relations
comprise the epistemic web: a network of texts, interpretations, and the people
who create those interpretations. As we build the epistemic web we are producing
not only a rich knowledge-base for the humanities, but also documenting the
scholarly process itself.

# Configuration

There are two configuration files in the ``/vogon/`` directory:

* ``heroku_settings.py``: Production configuration for Heroku.
* ``local_settings.py``: Development/testing configuration file.

If you're not deploying on Heroku, it's probably better to duplicate
``local_settings.py`` and go from there.

Select your preferred configuration with:

```shell
export DJANGO_SETTINGS_MODULE='vogon.my_settings_file'
```

See the [Django
documentation](https://docs.djangoproject.com/en/1.9/topics/settings/) for
information on the built-in configuration options.

VogonWeb needs several additional configuration parameters:

## Redis/Celery

Right now we're using Redis as the broker for Celery. You should set
``REDIS_URL`` in your environment, e.g.

```shell
export REDIS_URL="redis://"
```

## Conceptpower integration

VogonWeb expects the following settings for communication with the
Conceptpower authority service. The preferred approach is to set these in your
environment rather than hard-coding them in the config:

* ``CONCEPTPOWER_USERID`` - User in Conceptpower who can create concepts.
* ``CONCEPTPOWER_PASSWORD``
* ``CONCEPTPOWER_ENDPOINT`` - Full path to the REST endpoint, e.g.
  ``http://chps.asu.edu/conceptpower/rest/``

If your Conceptpower instance is using a custom namespace, you will also want to
set:

* ``CONCEPTPOWER_NAMESPACE`` - e.g. ``{http://www.digitalhps.org/}``

## Quadriga parameters

If you're using Quadriga to deposit annotation data, you'll need to set the
following parameters (again, preferably in your environment):

* ``QUADRIGA_USERID`` - A user who can create workspaces and submit networks.
* ``QUADRIGA_PASSWORD``
* ``QUADRIGA_ENDPOINT`` - Location of the Quadriga REST endpoint. e.g.  
  ``http://path.to.my/quadriga-test/rest/network``
* ``QUADRIGA_PROJECT`` - Default project to which VogonWeb will submit networks.
  This can be overridden on a per-project basis from within the VogonWeb admin
  interface.
* ``QUADRIGA_CLIENTID`` - An alphanumeric identifier for your VogonWeb instance.
  This is used to build client-specific project/workspace URLs in Quadriga.

## Amazon S3

VogonWeb uses an S3 bucket for some media (currently just user profile
pictures). Set the following three parameters in your environment:

* ``AWS_ACCESS_KEY``
* ``AWS_SECRET_KEY``
* ``S3_BUCKET``

## Elasticsearch/Haystack

VogonWeb uses Elasticsearch 2 for document search. Take a look at the Haystack
configuration section before deploying. For details, seeing the [Haystack
documentation](http://django-haystack.readthedocs.io/en/v2.4.1/settings.html).
It should look something like:

```
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'annotations.elasticsearch_backends.JHBElasticsearch2SearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'vogon',
    },
}
if not 'TRAVIS' in os.environ:
    HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
```

The ``RealtimeSignalProcessor`` is pretty aggressive. If you're deploying
without ES, consider commenting out that line.

# Deployment

VogonWeb is configured to deploy on the Heroku platform. Deploying it elsewhere
is pretty easy, too. The preferred approach is to serve it with Gunicorn behind
NGINX or Apache. See [this informative blog
post](http://michal.karzynski.pl/blog/2013/06/09/django-nginx-gunicorn-virtualenv-supervisor/)
for an example.

You'll want to set up two separate processes: one to run the webapp itself (e.g.
with Gunicorn), and another to execute Celery tasks. On Heroku we use these two
processes:

* ``web: gunicorn vogon.wsgi``
* ``worker: celery worker -B -A vogon``

The ``-B`` flag is for [periodic
tasks](http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html),
in this case a task that submits networks to Quadriga. You may want to remove
this flag if you're just getting started.

Both of these processes should be run with the environment variables described
above.

## Database backend

At a minimum, you'll need a database. VogonWeb has been tested with PostgresQL,
but most Django backends should work. See the [Django
documentation](https://docs.djangoproject.com/en/1.9/ref/databases/).

## Redis broker

A vanilla Redis server will work. You can read about using Redis with Celery [here](http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html).

## Elasticsearch 2.x

We use [Haystack](http://haystacksearch.org/) to interface with [Elasticsearch
2](https://www.elastic.co/). The current version of Haystack doesn't actually
support ES2 (the ES API changed dramatically), so we're using a custom backend
located in ``annotations/elasticsearch_backends.py``.

If you're using ES 1.x, the built-in ES backend for Haystack should work just
fine.
