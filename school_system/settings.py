# school_system/settings.py
import os
import dj_database_url
from urllib.parse import urlparse # Import urlparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- SECRET KEY - Load from env var ---
# IMPORTANT: Generate a NEW key for production and set it as env var on Koyeb
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-7#zm82-&1aus199$c=5q2i^@)b#*^@(*l=iyge&5^c+c4b#+r7' # Fallback ONLY for local dev if env var not set
)

# --- DEBUG - Load from env var ---
# Defaults to False if DJANGO_DEBUG is not 'True'
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'


# --- ALLOWED_HOSTS ---
# Start with an empty list
ALLOWED_HOSTS = []

# Get hosts from environment variable, split by comma
ALLOWED_HOSTS_STR = os.environ.get('DJANGO_ALLOWED_HOSTS')
if ALLOWED_HOSTS_STR:
    ALLOWED_HOSTS.extend(ALLOWED_HOSTS_STR.split(','))

# If in development (DEBUG=True), add local hosts.
# Ensure this block ONLY runs if DEBUG is actually True.
if DEBUG:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])

# If ALLOWED_HOSTS is still empty after checking env var and DEBUG,
# it means you are likely in production without setting the env var.
# This is a potential configuration error. Add a check or default if needed.
# For Koyeb deployment, ensure DJANGO_ALLOWED_HOSTS env var is set correctly.
if not ALLOWED_HOSTS and not DEBUG:
     print("WARNING: ALLOWED_HOSTS is empty in a non-DEBUG environment!")
     # Consider adding a default if absolutely necessary, but setting the env var is better.
     # ALLOWED_HOSTS = ['.koyeb.app'] # Example restrictive default - NOT recommended


# --- Application definition ---
INSTALLED_APPS = [
    'core',
    'import_export', # BEFORE admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Add this for simplified dev static serving
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # AFTER SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware', # Capital 'Mxxx'
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


# --- REVISED DATABASES SETTING ---
DATABASES = {}
DATABASE_URL = os.environ.get('DATABASE_URL')
print(f"DATABASE_URL detected: {DATABASE_URL}") # Keep for debug

if DATABASE_URL:
    # Parse the database URL provided by Render/Koyeb (or environment)
    db_config = dj_database_url.config(
        default=DATABASE_URL, # Use the env var
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=os.environ.get('DJANGO_DB_SSL_REQUIRE', 'False') == 'True'
    )

    # --- Manually Extract and Set the NAME ---
    try:
        # Parse the original URL string
        parsed_url = urlparse(DATABASE_URL)
        # Get the path (e.g., '/school_db_4cqb') and remove leading '/'
        db_name = parsed_url.path.lstrip('/')

        if db_name and len(db_name) <= 63:
            db_config['NAME'] = db_name # Override the NAME in the config dict
            print(f"DEBUG: Successfully extracted DB NAME: {db_name}")
        elif 'NAME' in db_config and len(db_config['NAME']) > 63:
            print(f"ERROR: Failed to parse DB name and dj-database-url default is too long: {db_config['NAME']}")
            # raise ImproperlyConfigured("Database name could not be parsed correctly and is too long.")
        else:
             print(f"WARNING: Could not extract DB name from path: {parsed_url.path}. Using dj-database-url default NAME.")

    except Exception as e:
         print(f"ERROR: Exception while parsing DATABASE_URL for NAME: {e}")
         # raise ImproperlyConfigured(f"Could not parse DATABASE_URL: {e}")

    DATABASES['default'] = db_config

else:
    # Fallback to SQLite if DATABASE_URL is not set (local development)
    print("WARNING: DATABASE_URL environment variable not set. Falling back to SQLite.")
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
# --- END REVISED DATABASES SETTING ---


# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    # ... keep validators ...
]


# --- Internationalization ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --- Static files (CSS, JavaScript, Images) ---
STATIC_URL = '/static/' # Must end with /
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Use Whitenoise storage for production (make sure DEBUG=False for this to be fully effective)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# --- Default primary key field type ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Authentication settings ---
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# --- Email settings (development) ---
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# --- CSRF trusted origins ---
CSRF_TRUSTED_ORIGINS_STR = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS')
if CSRF_TRUSTED_ORIGINS_STR:
    CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS_STR.split(',')
else:
    CSRF_TRUSTED_ORIGINS = []

# --- Security settings for HTTPS ---
# Ensure these env vars are set to 'True' on Koyeb
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', 'False') == 'True'

# Optional HSTS Settings (Read docs before enabling)
# SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', 0))
# SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False') == 'True'
# SECURE_HSTS_PRELOAD = os.environ.get('DJANGO_SECURE_HSTS_PRELOAD', 'False') == 'True'