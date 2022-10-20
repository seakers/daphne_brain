"""
Django settings for daphne_brain project.
Generated by 'django-admin startproject' using Django 1.10.6.
For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'aaaaa'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False


# ALLOWED_HOSTS = [
#     '3.128.235.245',
#     '18.191.17.82'
#     '127.0.0.1',
#     'localhost',
#     'daphne',
#     'daphne_brain',
#     'www.selva-research.com',
#     'dev.selva-research.com',
#     'prod.selva-research.com',
#     'selva-research.engr.tamu.edu',
#     'daphne-at-dev.selva-research.com',
#     'daphne-at.selva-research.com',
#     'brain',
#     'daphne-dev-bucket.s3-website.us-east-2.amazonaws.com',
#     'daphne-dev-load-balancer-1316892040.us-east-2.elb.amazonaws.com',
#     'daphne-dev-services.selva-research.com'
# ]
ALLOWED_HOSTS = [
    '*'
]

USE_X_FORWARDED_HOST = True

ACTIVE_MODULES = ['EOSS']


EDL_PATH = '/Users/ssantini/Code/'
INSTALLED_APPS = [

    # Installed Packages
    'channels',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',

    # Seaklab APIs
    'auth_API',
    'daphne_context',
    'example_problem',
    'EOSS',
    'EDL',
    'AT',
    'experiment',
    'experiment_at',
    'iFEED_API',

]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'daphne_brain.tamu_subdomains_session.TamuSubdomainsSessionMiddleware',
    'daphne_brain.HealthCheckMiddleware.HealthCheckMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'daphne_brain.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'daphne_brain.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'daphne',
        'USER': os.environ['SQL_USER'],
        'PASSWORD': os.environ['SQL_PASSWORD'],
        'HOST': os.environ['POSTGRES_HOST'],
        'PORT': os.environ['POSTGRES_PORT'],
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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

# CORS & CSRF


# SESSION_COOKIE_DOMAIN = '.s3-website.us-east-2.amazonaws.com'
# CSRF_COOKIE_DOMAIN = '.s3-website.us-east-2.amazonaws.com'

if os.environ['DEPLOYMENT_TYPE'] == 'aws':
    # CSRF_COOKIE_SECURE = True
    # CSRF_COOKIE_SAMESITE = 'None'
    CSRF_COOKIE_DOMAIN = '.selva-research.com'
    # SESSION_COOKIE_SECURE = True
    # SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_DOMAIN = '.selva-research.com'



CORS_ALLOW_ALL_ORIGINS = True
CORS_ORIGIN_WHITELIST = (
    'http://daphne.engr.tamu.edu',
    'http://localhost:8080',
    'http://dev.selva-research.com',
    'http://prod.selva-research.com',
    'http://daphne-dev-bucket.selva-research.com',
    'http://daphne-dev-load-balancer-1316892040.us-east-2.elb.amazonaws.com',
    'https://daphne-dev-load-balancer-1316892040.us-east-2.elb.amazonaws.com',
    'http://daphne-dev-services.selva-research.com:8000',
    'https://daphne-dev-services.selva-research.com:443'
)
CORS_ALLOW_CREDENTIALS = True


CSRF_TRUSTED_ORIGINS = (
    'http://daphne.engr.tamu.edu',
    'http://localhost:8080',
    'http://dev.selva-research.com',
    'http://prod.selva-research.com',
    'http://daphne-dev-bucket.selva-research.com',
    'http://daphne-dev-load-balancer-1316892040.us-east-2.elb.amazonaws.com',
    'https://daphne-dev-load-balancer-1316892040.us-east-2.elb.amazonaws.com',
    'https://daphne-dev-services.selva-research.com:443',
    'http://daphne-dev-services.selva-research.com:8000'
)


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Chicago'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ['REDIS_HOST'], os.environ['REDIS_PORT'])],
        }
    },
}

# ASGI_APPLICATION should be set to your outermost router
ASGI_APPLICATION = 'daphne_brain.asgi.application'

# Databases for Daphne
ALCHEMY_DATABASE = {
    'drivername': 'postgresql+psycopg2',
    'host': os.environ['POSTGRES_HOST'],
    'port': os.environ['POSTGRES_PORT'],
    'username': os.environ['SQL_USER'],
    'password': os.environ['SQL_PASSWORD'],
    'database': 'daphne'
}

EDL_DATABASE = {
    'drivername': 'postgresql+psycopg2',
    'host': os.environ['POSTGRES_HOST'],
    'port': os.environ['POSTGRES_PORT'],
    'username': os.environ['SQL_USER'],
    'password': os.environ['SQL_PASSWORD'],
    'database': 'edldatabase'
}

ECLSS_DATABASE = {
    'drivername': 'postgres',
    'host': 'www.selva-research.com',
    'port': '5432',
    'username': os.environ['SQL_USER'],
    'password': os.environ['SQL_PASSWORD'],
    'database': 'eclss'
}





# Session configuration
# SESSION_ENGINE = "merge_session.merge_db"

# Email

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = 'Daphne Admin <daphne@selva-research.com>'

# AWS
DEPLOYMENT_TYPE = os.environ['DEPLOYMENT_TYPE']

# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] - %(name)s - %(levelname)s - %(message)s'
        },
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%Y/%m/%d %H:%M:%S"
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR + '/logs/daphne.log',
            'formatter': 'standard',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        # 'WARNING': {
        #     'handlers': ['file', 'console'],
        #     'level': 'WARNING',
        #     'propagate': True,
        # },
        # 'INFO': {
        #     'handlers': ['file', 'console'],
        #     'level': 'INFO',
        #     'propagate': True,
        # },
        'iFEED': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'VASSAR': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'critic': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'data-mining': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'debugging': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'config': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}