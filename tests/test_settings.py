# Minimal settings file required to run tests.

from ctypes.util import find_library

# MacOSX + Homebrew
SPATIALITE_LIBRARY_PATH = find_library('mod_spatialite')
# Probably everything else
# SPATIALITE_LIBRARY_PATH = find_library('spatialite')

SECRET_KEY = 'poodles-puddles'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',

    'tests',
    'scenarios',
    'visualize',
    'drawing',
    'mapgroups',
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': 'some.db',
    }
}

USE_TZ = True

ROOT_URLCONF = 'tests.urls'

SHARING_TO_PUBLIC_GROUPS = ['Share with Public']
SHARING_TO_STAFF_GROUPS = ['Share with Staff']

GEOMETRY_CLIENT_SRID = 4326
GEOMETRY_DB_SRID = 4326