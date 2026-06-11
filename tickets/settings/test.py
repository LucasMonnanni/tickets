import os


os.environ.setdefault('SECRET', 'test-secret-key')
os.environ.setdefault('SYTEX_URL', 'https://example.com')
os.environ.setdefault('SYTEX_USER', 'test-user')
os.environ.setdefault('SYTEX_PASSWORD', 'test-password')
os.environ.setdefault('BLUETOOTH_URL', 'https://example.com')
os.environ.setdefault('BLUETOOTH_USER', 'test-user')
os.environ.setdefault('BLUETOOTH_PASSWORD', 'test-password')

from .base import *


DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': ':memory:',
	}
}

PASSWORD_HASHERS = [
	'django.contrib.auth.hashers.MD5PasswordHasher',
]

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

RECAPTCHA_PUBLIC_KEY = 'test'
RECAPTCHA_PRIVATE_KEY = 'test'
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']

# Dict comprehension setting all app migrations to None
MIGRATION_MODULES = {
    app.split('.')[-1]: None 
    for app in INSTALLED_APPS
}

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
