"""
Django settings for tickets project.

Updated for Django 5.2
"""
import os
import environ


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'), overwrite=True)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET', str)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tkts',
    'sitios',
    'logger',
    'ntfcs',
    'django_recaptcha',
    'import_export',
    'django_ckeditor_5',
	'after_response'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'tickets.middleware.NavContextMiddleware',
]

ROOT_URLCONF = 'tickets.urls'

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

WSGI_APPLICATION = 'tickets.wsgi.application'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
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

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = "/"

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'es-AR'

TIME_ZONE = 'America/Argentina/Buenos_Aires'

USE_I18N = True

USE_L10N = True

DATE_INPUT_FORMATS = [
     '%d/%m/%Y', '%d/%m/%y',
]

USE_TZ = True

STORAGES = {
	"staticfiles": {
	    "BACKEND": 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    }
}
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

CKEDITOR_5_CONFIGS = {
    'notificacion': {
        'width': '100%',
    },
}

SYTEX_API = {
    'URL': env('SYTEX_URL'),
    'USER': env('SYTEX_USER'),
    'PASSWORD': env('SYTEX_PASSWORD')
}

BLUETOOTH_API = {
    'URL': env('BLUETOOTH_URL'),
    'USER': env('BLUETOOTH_USER'),
    'PASSWORD': env('BLUETOOTH_PASSWORD')
}