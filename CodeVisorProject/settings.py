
from pathlib import Path
import os, base64
from decouple import config
from imagekitio import ImageKit
from urllib.parse import urlparse, parse_qsl



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-t1ft4_k1_-*amy(=1n!e^0)@5ifrxqo-tnywsgz#b^z1&qyxfk'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'daphne',
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'AuthApp.apps.AuthappConfig',
    'BlogApp.apps.BlogappConfig',
    'BattleApp',
    'PracticeApp',
    'AIChatbotApp',
    'PyCompilerApp',
    'JobsApp',
    'ckeditor',
    'comment',
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

ROOT_URLCONF = 'CodeVisorProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'CodeVisorProject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases


# encoded_cert = config("CA_CERT")
# if encoded_cert:
#     cert_path = os.path.join(
#         BASE_DIR,
#         'db_cert.pem'
#     )
#     with open(cert_path, 'wb') as file:
#         file.write(base64.b64decode(encoded_cert))

# else:
#     cert_path = None
    

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': config("DB_NAME"),           
#         'USER': config("DB_USER"),            
#         'PASSWORD': config("DB_PASSWORD"),
#         'HOST': config("DB_HOST"),
#         'PORT': config("DB_PORT"),               
#         'OPTIONS': {
#             'init_command': "SET SESSION tidb_txn_mode = 'pessimistic';",
#             'ssl': {
#                 'ca': cert_path,
#             }
#         },
        
#     }
# }



# Replace the DATABASES section of your settings.py with this
tmpPostgres = urlparse(config('DATABASE_URL', cast=str))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': tmpPostgres.path.replace('/', ''),
        'USER': tmpPostgres.username,
        'PASSWORD': tmpPostgres.password,
        'HOST': tmpPostgres.hostname,
        'PORT': 5432,
        'OPTIONS': dict(parse_qsl(tmpPostgres.query)),
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ASGI_APPLICATION = 'CodeVisorProject.asgi.application'
# manual configurations beyond this line

# setup for uploading media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ckeditor configurations
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        # 'height': '720px',
        # 'width': "640px",
    },
}

LOGIN_URL = '/auth/login'
LOGOUT_REDIRECT_URL =  '/auth/login'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = config("EMAIL_HOST_USER")

STATICFILES_DIRS = [
    os.path.join(
        BASE_DIR,
        'static'
    )
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# imagekit.io object initialization
imagekit = ImageKit(
    private_key=config("IMAGEKIT_PRIV_KEY"),
    public_key=config("IMAGEKIT_PUB_KEY"),
    url_endpoint=config("IMAGEKIT_URL")
)

# django comments dab setup
PROFILE_APP_NAME = 'AuthApp'
PROFILE_MODEL_NAME = 'Profile'
MAX_THREAD_LEVEL = 5
COMMENTS_DAB_MAX_THREAD_LEVEL = 3
