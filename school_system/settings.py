import os
import dj_database_url
from urllib.parse import urlparse
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Secret key
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-7#zm82-&1aus199$c=5q2i^@)b#*^@(*l=iyge&5^c+c4b#+r7'
)

# Debug mode
#DEBUG = os.environ.get('DJANGO_DEBUG', '').lower() in ['true', '1', 'yes']
DEBUG=True

# Allowed hosts
ALLOWED_HOSTS = []
raw_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '')

if raw_hosts:
    for entry in raw_hosts.split(','):
        host = entry.strip()
        if not host:
            continue
        # Strip protocol if provided
        if host.startswith('http://') or host.startswith('https://'):
            parsed = urlparse(host)
            host = parsed.hostname or host
        ALLOWED_HOSTS.append(host)

if DEBUG:
    # Always allow localhost in debug mode
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])

if not ALLOWED_HOSTS and not DEBUG:
    raise RuntimeError(
        'ALLOWED_HOSTS is empty. Set DJANGO_ALLOWED_HOSTS env var to include your domain.'
    )

# Application definition
INSTALLED_APPS = [
    'core',
    'import_export',  # import-export before admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'school_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'school_system.wsgi.application'

# Database configuration
db_url = os.environ.get('DATABASE_URL')
if db_url:
    parsed_url = urlparse(db_url)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed_url.path.lstrip('/'),
            'USER': parsed_url.username,
            'PASSWORD': parsed_url.password,
            'HOST': parsed_url.hostname,
            'PORT': parsed_url.port or '',
            'CONN_MAX_AGE': 600,
            **({ 'OPTIONS': { 'sslmode': 'require' }}
               if os.environ.get('DJANGO_DB_SSL_REQUIRE', 'False') == 'True' else {})
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator' },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default auto field
default_auto_field = 'django.db.models.BigAutoField'

# Authentication redirects
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CSRF trusted origins
raw_csrf = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in raw_csrf.split(',') if o.strip()]

# Security settings for HTTPS
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', 'False') == 'True'

# Proxy settings
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
