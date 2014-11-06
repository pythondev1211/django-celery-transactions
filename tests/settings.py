__doc__ = """Minimal django settings to run manage.py test command"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': __name__,
    }
}

BROKER_BACKEND = 'memory'

ROOT_URLCONF = 'tests.urls'

from celery import current_app
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
current_app.conf.CELERY_ALWAYS_EAGER = True
current_app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True


INSTALLED_APPS = ('djcelery_transactions',
                  'test'
                  )

SECRET_KEY = "django_tests_secret_key"
TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
ADMIN_MEDIA_PREFIX = '/static/admin/'
STATICFILES_DIRS = ()

TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner'