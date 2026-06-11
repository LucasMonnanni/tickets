import os

# Provide fallbacks so Django can import settings on Render
# without requiring a full .env configuration.
os.environ.setdefault('SECRET', 'demo-secret-key-change-me')

os.environ.setdefault('SYTEX_URL', 'https://example.com')
os.environ.setdefault('SYTEX_USER', 'demo-user')
os.environ.setdefault('SYTEX_PASSWORD', 'demo-password')

os.environ.setdefault('BLUETOOTH_URL', 'https://example.com')
os.environ.setdefault('BLUETOOTH_USER', 'demo-user')
os.environ.setdefault('BLUETOOTH_PASSWORD', 'demo-password')

from .base import *


DEBUG = False

# Render apps are typically served via *.onrender.com; keep this permissive for demo.
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Avoid system-check failures when using demo captcha keys.
RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', 'test')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', 'test')
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# If Render sends requests through a proxy, this helps Django generate correct HTTPS URLs.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
