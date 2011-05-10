import os.path

DEBUG = True
TEMPLATE_DEBUG = True

# SETTINGS_DIR allows media paths and so to be relative to this settings file
# instead of hardcoded to c:\only\on\my\computer.
SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))

# BUILDOUT_DIR is for access to the "surrounding" buildout, for instance for
# BUILDOUT_DIR/var/static files to give django-staticfiles a proper place
# to place all collected static files.
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))

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
        'ENGINE': 'sqlite3',
        'NAME': 'test.db',
        },
    'fews-unblobbed': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BUILDOUT_DIR, 'fews_unblobbed_readwrite.db')
        },
    }


SITE_ID = 1
INSTALLED_APPS = [
    'lizard_waterbalance',
    'lizard_fewsunblobbed',
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

DATABASE_ROUTERS = ['lizard_fewsunblobbed.routers.FewsUnblobbedRouter', ]

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
