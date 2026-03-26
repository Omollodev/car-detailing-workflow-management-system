"""
Django settings for Car Detailing Workflow Management System.

For production deployment, ensure all security settings are properly configured
and sensitive values are loaded from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-this-in-production-xyz123')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

def _parse_csv_env(name, default):
    """
    Parse comma-separated env values and normalize common formatting issues.
    This avoids runtime issues from accidental spaces or quoted entries.
    """
    raw_value = os.getenv(name, default)
    return [item.strip().strip("'\"") for item in raw_value.split(',') if item.strip()]


ALLOWED_HOSTS = _parse_csv_env(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1,car-detailing-workflow-management-system-production.up.railway.app'
)
CSRF_TRUSTED_ORIGINS = _parse_csv_env(
    'CSRF_TRUSTED_ORIGINS',
    'https://localhost,https://127.0.0.1,https://car-detailing-workflow-management-system-production.up.railway.app'
)

# Application definition
INSTALLED_APPS = [
    'daphne',
    'channels',
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # installed frameworks
    "crispy_forms",
    "crispy_bootstrap5",
    
    # Local apps
    'apps.accounts',
    'apps.customers',
    'apps.jobs',
    'apps.services',
    'apps.workers',
    'apps.dashboard',
    'apps.notifications',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.notifications.context_processors.unread_notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# Use DATABASE_URL when valid, otherwise fall back to local sqlite.
# Database configuration
# Railway/production: prefer private DATABASE_URL, then public proxy URL.
database_url = (
    os.getenv('DATABASE_URL')
    or os.getenv('DATABASE_PUBLIC_URL')
    or ''
).strip()

# In production, we MUST have a valid DATABASE_URL
if database_url and database_url != '://':
    try:
        DATABASES = {
            'default': dj_database_url.parse(database_url, conn_max_age=600)
        }
        # Add connection health check for production
        if not DEBUG:
            DATABASES['default']['CONN_MAX_AGE'] = 600
            DATABASES['default']['CONN_HEALTH_CHECKS'] = True
    except Exception as e:
        if DEBUG:
            # In development, fall back to SQLite
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / 'db.sqlite3',
                }
            }
        else:
            # In production, fail loudly
            raise Exception(f"Invalid DATABASE_URL/DATABASE_PUBLIC_URL configuration: {e}")
else:
    if DEBUG:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
    else:
        raise Exception(
            "DATABASE_URL (or DATABASE_PUBLIC_URL) environment variable is required in production"
        )



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


# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# django-crispy-forms + crispy-bootstrap5
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (User uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Messages framework
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# AJAX Polling interval (in milliseconds)
# Staff notification dropdown polling (ms); lower = faster manager/worker updates
AJAX_POLLING_INTERVAL = 12000

# Business Configuration
BUSINESS_NAME = os.getenv('BUSINESS_NAME')
BUSINESS_PHONE = os.getenv('BUSINESS_PHONE')
BUSINESS_EMAIL = os.getenv('BUSINESS_EMAIL')
BUSINESS_ADDRESS = os.getenv('BUSINESS_ADDRESS')

# Email (customer welcome / notifications). Use SMTP in production.
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587') or '587')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv(
    'DEFAULT_FROM_EMAIL',
    os.getenv('BUSINESS_EMAIL', 'noreply@localhost'),
)

# Optional SMS after registration (Africa's Talking — common in Kenya)
REGISTRATION_SMS_ENABLED = os.getenv(
    'REGISTRATION_SMS_ENABLED', 'False'
).lower() in ('true', '1', 'yes')
AT_USERNAME = os.getenv('AT_USERNAME', '')
AT_API_KEY = os.getenv('AT_API_KEY', '')

# M-Pesa Daraja — STK Push (Lipa na M-Pesa Online)
MPESA_DARAJA_ENABLED = os.getenv(
    'MPESA_DARAJA_ENABLED', 'False'
).lower() in ('true', '1', 'yes')
MPESA_ENV = os.getenv('MPESA_ENV')
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE', '')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY', '')
# Paybill/till number for PartyB if different from BusinessShortCode (Till / Buy Goods)
MPESA_PARTY_B = os.getenv('MPESA_PARTY_B', '')
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL', '')
MPESA_TRANSACTION_TYPE = os.getenv(
    'MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline'
)
MPESA_INITIATOR = os.getenv('MPESA_INITIATOR')
MPESA_SECURITY_CREDENTIAL = os.getenv('MPESA_SECURITY_CREDENTIAL', '')
MPESA_B2B_COMMAND_ID = os.getenv('MPESA_B2B_COMMAND_ID', 'BusinessPayBill')
MPESA_SENDER_IDENTIFIER_TYPE = os.getenv('MPESA_SENDER_IDENTIFIER_TYPE', '4')
MPESA_RECEIVER_IDENTIFIER_TYPE = os.getenv('MPESA_RECEIVER_IDENTIFIER_TYPE', '4')
MPESA_REQUESTER = os.getenv('MPESA_REQUESTER', '')
MPESA_QUEUE_TIMEOUT_URL = os.getenv('MPESA_QUEUE_TIMEOUT_URL', MPESA_CALLBACK_URL)
MPESA_RESULT_URL = os.getenv('MPESA_RESULT_URL', MPESA_CALLBACK_URL)

# Security settings for production
if not DEBUG:
    # Heroku / Render / proxies terminate TLS — avoid redirect loops
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# Jazzmin (Admin UI) - clearer app differentiation
JAZZMIN_SETTINGS = {
    "site_title": "DetailFlow Admin",
    "site_header": "DetailFlow",
    "site_brand": "DetailFlow",
    "welcome_sign": "Welcome to DetailFlow Administration",
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": [
        "accounts",
        "customers",
        "jobs",
        "services",
        "workers",
        "notifications",
    ],
    "icons": {
        "accounts.User": "fas fa-user-shield",
        "customers.Customer": "fas fa-users",
        "customers.Vehicle": "fas fa-car",
        "jobs.Job": "fas fa-clipboard-list",
        "jobs.JobService": "fas fa-tasks",
        "services.Service": "fas fa-concierge-bell",
        "workers.WorkerProfile": "fas fa-user-hard-hat",
        "notifications.Notification": "fas fa-bell",
    },
    "custom_links": {
        "jobs": [
            {
                "name": "Dashboard",
                "url": "dashboard:index",
                "icon": "fas fa-chart-line",
                "permissions": ["jobs.view_job"],
            }
        ]
    },
}



