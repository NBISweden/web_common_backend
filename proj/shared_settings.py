"""
Shared settings

Django settings for the project 'proj'

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
import logging
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
PARENT_DIR = os.path.realpath("%s/../"%(BASE_DIR))
apppath =  "%s/pred/app/"%(BASE_DIR)
path_log = "%s/pred/static/log"%(BASE_DIR)
logfile = "%s/load_settings.log"%(path_log)
sys.path.append(apppath)
import myfunc
import webserver_common as webcom

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djangojs',
    'eztables',
    'proj.pred'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'proj.urls'

WSGI_APPLICATION = 'proj.wsgi.application'

LOGIN_REDIRECT_URL = '/pred'
LOGOUT_REDIRECT_URL = '/pred/login'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PARENT_DIR, 'db.sqlite3'),
    },
}
TEMPLATES = [ 
    {   
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'pred', 'templates'),
            os.path.join(BASE_DIR, 'pred', 'static'),
            ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],  
        },  
    },  
]

# LOGGING configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "%s/%s/%s/%s/debug.log"%(BASE_DIR,"pred", "static", "log"),
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'root': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'proj.pred.views': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
logging.basicConfig(level=logging.DEBUG)
#logging.getLogger('spyne.protocol.xml').setLevel(logging.DEBUG)

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
SUPER_USER_LIST = ["admin","nanjiang", "njshu"]

ALLOWED_HOSTS = ['localhost', 'dev.commonbackend.*', 'commonbackend.*', 'commonbackend.computenode.pcons3.se', 'commonbackend.computenode.shu.se']

computenodefile = "%s/pred/config/computenode.txt"%(BASE_DIR)
if os.path.exists(computenodefile):
    nodelist = []
    try:
        nodelist = myfunc.ReadIDList2(computenodefile,col=0)
    except:
        pass
    ALLOWED_HOSTS += nodelist

# add also the IP of the host to ALLOWED_HOSTS
try:
    cmd = ["bash", "%s/get_ext_ip_address_cloud.sh"%(apppath)]
    ipaddress = subprocess.check_output(cmd)
    ALLOWED_HOSTS.append(ipaddress)
    webcom.loginfo("IP address: %s"%(ipaddress), logfile)
except:
    webcom.loginfo("failed to get ip address", logfile)
    pass

ALLOWED_HOSTS = list(set(ALLOWED_HOSTS))
