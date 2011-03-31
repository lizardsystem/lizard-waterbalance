DEBUG = True
TEMPLATE_DEBUG = True

#DATABASE_ENGINE = 'sqlite3'
#DATABASE_NAME = 'test.db'

DATABASES = {
    # If you want to use another database, consider putting the database
    # settings in localsettings.py. Otherwise, if you change the settings in
    # the current file and commit them to the repository, other developers will
    # also use these settings whether they have that database or not.
    #
    # One of those other developers is Jenkins, our continuous integration
    # solution. Jenkins can only run the tests of the current application when
    # the specified database exists. When the tests cannot run, Jenkins sees
    # that as an error.
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': '127.0.0.1',
        'NAME': 'waterbalance',
        'USER': 'buildout',
        'PASSWORD': 'buildout'
        },
    }


SITE_ID = 1
INSTALLED_APPS = [
    'lizard_waterbalance',
    'lizard_map',
    'lizard_ui',
    #'south',
    'staticfiles',
    'compressor',
    'django_extensions',
    'django_nose',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    ]
ROOT_URLCONF = 'lizard_waterbalance.urls'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Used for django-staticfiles
STATIC_URL = '/static_media/'
TEMPLATE_CONTEXT_PROCESSORS = (
    # Default items.
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    # Needs to be added for django-staticfiles to allow you to use
    # {{ STATIC_URL }}myapp/my.css in your templates.
    'staticfiles.context_processors.static_url',
    )


try:
    # Import local settings that aren't stored in svn.
    from lizard_waterbalance.local_testsettings import *
except ImportError:
    pass
