from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    'localhost'
]

INSTALLED_APPS += [
    'debug_toolbar',
	'template_profiler_panel'
]

MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

INTERNAL_IPS = [
    "127.0.0.1",
]

DEBUG_TOOLBAR_CONFIG = {
	'IS_RUNNING_TESTS': False
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tickets_dev',
        'USER': 'ticketsArg',
        'PASSWORD': 'X6a1h7h[jSF8N.L5',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES',
        },
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.history.HistoryPanel',
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
	'template_profiler_panel.panels.template.TemplateProfilerPanel',
]