"""
Django settings for api project.

Generated by 'django-admin startproject' using Django 5.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
Author: Martin Luther
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-utr163745j!iq*)7h-+g6_!y+z$mkmcx3x2ouv$gq$8-42)yn+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    f"{os.environ.get('DOMAIN1', '')}.boostedchat.com",
    f"{os.environ.get('DOMAIN2', '')}.boostedchat.com",
    f"scrapper.{os.environ.get('DOMAIN1', '')}.boostedchat.com",
    f"airflow.{os.environ.get('DOMAIN1', '')}.boostedchat.com",
    f"scrapper.{os.environ.get('DOMAIN2', '')}.boostedchat.com",
    f"airflow.{os.environ.get('DOMAIN2', '')}.boostedchat.com",
    "34.28.104.255",
    "127.0.0.1",
    "0.0.0.0",
    "localhost",
    "web",
    "booksy.us.boostedchat.com",
    "scrapper.booksy.boostedchat.com",
    "airflow.booksy.boostedchat.com",
]
CSRF_TRUSTED_ORIGINS = [
    f"https://api.{os.environ.get('DOMAIN1', '')}.boostedchat.com",
    f"https://api.{os.environ.get('DOMAIN2', '')}.boostedchat.com",
    f"https://scrapper.{os.environ.get('DOMAIN1', '')}.boostedchat.com",
    f"https://scrapper.{os.environ.get('DOMAIN2', '')}.boostedchat.com",
    "http://34.28.104.255"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api.instagram',
    'api.scout',
    'api.helpers',
    'rest_framework',
    'django_celery_beat',
    'softdelete',
    'boostedchatScrapper',
    'sitemaps'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'api.urls'


TEMPLATES = [
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

WSGI_APPLICATION = 'api.wsgi.application'

AIRFLOW_API_BASE_URL = 'http://localhost:8080/api/v1'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DBNAME_ETL").strip(),
        "USER": os.getenv("POSTGRES_USERNAME_ETL").strip(),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD_ETL").strip(),
        "HOST": os.getenv("POSTGRES_HOST_ETL").strip(),
        "PORT": os.getenv("POSTGRES_PORT_ETL").strip(),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CRISPY_TEMPLATE_PACK = "bootstrap4"
MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY").strip()
MAILCHIMP_DATA_CENTER = os.getenv("MAILCHIMP_DATA_CENTER").strip()
MAILCHIMP_EMAIL_LIST_ID = os.getenv("MAILCHIMP_EMAIL_LIST_ID").strip()
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_HOST_USER").strip()

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER").strip()
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD").strip()
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = '/usr/src/app/static'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    f"https://{os.environ.get('DOMAIN1', '')}.boostedchat.com",
    f"https://{os.environ.get('DOMAIN2', '')}.boostedchat.com",
    "http://localhost:8080",
    "http://127.0.0.1:9000",
    "http://localhost:9000",
    "http://localhost:5173",
    "https://booksy.us.boostedchat.com",
    "https://jamel.boostedchat.com"
]

CORS_ALLOW_HEADERS = (
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
)


CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)

AI_MICROSERVICE_URL = "http://34.170.152.34/modelhub/"
