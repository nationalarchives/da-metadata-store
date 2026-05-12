"""
Django settings for store project.
"""

import os
from pathlib import Path
from sysconfig import get_path

from django.conf.global_settings import APPEND_SLASH
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-change-me")
DEBUG = os.environ.get("DEBUG", "False") == "True"

APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000").rstrip("/")

if not DEBUG:
    ALLOWED_HOSTS = [APP_BASE_URL.split("//")[1], "xth7tebpt8.execute-api.eu-west-2.amazonaws.com"]
else:
    ALLOWED_HOSTS = ["localhost"]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'saml_auth',
    'store'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'store.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [
            BASE_DIR / "templates",
            "tna_frontend_jinja/templates",
        ],
        "APP_DIRS": True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ]
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'store.wsgi.application'

# Lambda Function URL events include stage="$default" in requestContext, which
# causes Zappa to set SCRIPT_NAME="/$default". Override it to keep URLs clean.
FORCE_SCRIPT_NAME = ""


# Database

import dj_database_url

_db = dj_database_url.config(
    default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    conn_max_age=0,  # Never pool — each connection gets a fresh IAM token
)
# Swap in the IAM-aware backend when connecting to PostgreSQL
if _db.get("ENGINE") == "django.db.backends.postgresql":
    _db["ENGINE"] = "store.db_backend"

DATABASES = {"default": _db}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

APPEND_SLASH = False
LOGIN_URL = '/saml/login'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# ------------------------------------------------------------------
# SAML settings — consumed by saml_auth/saml_utils.py
# ------------------------------------------------------------------
SAML_IDP_ENTITY_ID = os.environ.get("SAML_IDP_ENTITY_ID", "")
SAML_IDP_SSO_URL = os.environ.get("SAML_IDP_SSO_URL", "")
SAML_IDP_SLO_URL = os.environ.get("SAML_IDP_SLO_URL", "")
SAML_IDP_CERT = os.environ.get("SAML_IDP_CERT", "")
