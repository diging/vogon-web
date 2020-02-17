"""
Django settings for vogon project.

Generated by 'django-admin startproject' using Django 1.8.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os, sys, requests
from urllib.parse  import urlparse
import socket
import dj_database_url
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'secretsecret')

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = eval(os.environ.get('DEBUG', 'False'))
DEBUG=True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'concepts',
    'giles',
    'rest_framework',
    'corsheaders',
    'repository',
    'annotations',
    'accounts',
    'goat'
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ROOT_URLCONF = 'vogon.urls'

SITE_ID = 1

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "annotations/templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'annotations.context_processors.google',
                'annotations.context_processors.version',
                'annotations.context_processors.base_url',
            ],
        },
    },
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (   
        #'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json'
}

WSGI_APPLICATION = 'vogon.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {'default': dj_database_url.config()}
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'

# print DATABASES

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # default
    # 'social.backends.github.GithubOAuth2',
    #'allauth.account.auth_backends.AuthenticationBackend',
)

ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS =True
ANONYMOUS_USER_ID = -1
BASE_URL = os.environ.get('BASE_URL', '/')

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

APPEND_SLASH = False
CRISPY_TEMPLATE_PACK = 'bootstrap3'

SUBPATH = '/'
# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers


# Static asset configuration
BASE_PATH = os.environ.get('BASE_PATH', '/')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.environ.get('STATIC_ROOT',
                             os.path.join(PROJECT_ROOT, 'staticfiles'))
STATIC_URL = BASE_URL + 'static/'

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'), )

JARS_KEY = '050814a54ac5c81b990140c3c43278031d391676'
AUTH_USER_MODEL = 'annotations.VogonUser'

es = urlparse(os.environ.get('SEARCHBOX_URL') or 'http://127.0.0.1:9200/')
port = es.port or 80


TEMPORAL_PREDICATES = {
    'start':
    'http://www.digitalhps.org/concepts/CONbbbb0940-84be-4450-b92f-557a78249ebd',
    'end':
    'http://www.digitalhps.org/concepts/CONbfd1fc2d-0393-4bdb-92f5-7500cdc507f8',
    'occur':
    'http://www.digitalhps.org/concepts/ba626314-5d54-41b6-8f41-0013be5269be'
}

BROKER_POOL_LIMIT = 0

PREDICATES = {
    'have':
    'http://www.digitalhps.org/concepts/CON83f5110b-5034-4c95-82f8-8f80ff55a1b9',
    'be':
    'http://www.digitalhps.org/concepts/CON3fbc4870-6028-4255-9998-14acf028a316'
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'default_cache_table',
    }
}

CONCEPTPOWER_USERID = os.environ.get('CONCEPTPOWER_USERID', None)
CONCEPTPOWER_PASSWORD = os.environ.get('CONCEPTPOWER_PASSWORD', None)
CONCEPTPOWER_ENDPOINT = os.environ.get(
    'CONCEPTPOWER_ENDPOINT', 'http://chps.asu.edu/conceptpower/rest/')
CONCEPTPOWER_NAMESPACE = os.environ.get('CONCEPTPOWER_NAMESPACE',
                                        '{http://www.digitalhps.org/}')

QUADRIGA_USERID = os.environ.get('QUADRIGA_USERID', '')
QUADRIGA_PASSWORD = os.environ.get('QUADRIGA_PASSWORD', '')
QUADRIGA_ENDPOINT = os.environ.get('QUADRIGA_ENDPOINT', '')
QUADRIGA_CLIENTID = os.environ.get('QUADRIGA_CLIENTID', 'vogonweb')
QUADRIGA_PROJECT = os.environ.get('QUADRIGA_PROJECT', 'vogonweb')

BASE_URI_NAMESPACE = u'http://www.vogonweb.net'

GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', None)

VERSION = '0.4'

# Giles and HTTP.
GILES = os.environ.get('GILES', 'https://diging-dev.asu.edu/giles-review')
IMAGE_AFFIXES = ['png', 'jpg', 'jpeg', 'tiff', 'tif']
GET = requests.get
POST = requests.post
GILES_APP_TOKEN = os.environ.get('GILES_APP_TOKEN', 'nope')
GILES_DEFAULT_PROVIDER = os.environ.get('GILES_DEFAULT_PROVIDER', 'github')
MAX_GILES_UPLOADS = 20

GOAT = os.environ.get('GOAT', 'http://127.0.0.1:8000')
GOAT_APP_TOKEN = os.environ.get('GOAT_APP_TOKEN')

# LOGIN_REDIRECT_URL = 'home'
# LOGOUT_REDIRECT_URL = 'home'

LOGLEVEL = os.environ.get('LOGLEVEL', 'DEBUG')

SESSION_COOKIE_NAME = 'vogon'

# Concept types
PERSONAL_CONCEPT_TYPE = os.environ.get('PERSONAL_CONCEPT_TYPE',
                                       '986a7cc9-c0c1-4720-b344-853f08c136ab')
CORPORATE_CONCEPT_TYPE = os.environ.get(
    'CORPORATE_CONCEPT_TYPE', '3fc436d0-26e7-472c-94de-0b712b66b3f3')
GEOGRAPHIC_CONCEPT_TYPE = os.environ.get(
    'GEOGRAPHIC_CONCEPT_TYPE', 'dfc95f97-f128-42ae-b54c-ee40333eae8c')

CONCEPT_TYPES = {
    'viaf:personal': PERSONAL_CONCEPT_TYPE,  # E21 Person
    'viaf:corporate': CORPORATE_CONCEPT_TYPE,  # E40 Legal Body
    'viaf:geographic': GEOGRAPHIC_CONCEPT_TYPE,  # E53 Place
}

SUBMIT_WAIT_TIME = {'days': 3, 'hours': 0, 'minutes': 0}

CORS_ALLOW_CREDENTIALS = True

CORS_ORIGIN_WHITELIST = [
    'http://localhost:8000',
    'http://localhost:8080',
	'http://127.0.0.1:8080'
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8080',
    'http://localhost:8000',
]

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=90),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '')
GITHUB_SECRET_ID = os.environ.get('GITHUB_SECRET_ID', '')