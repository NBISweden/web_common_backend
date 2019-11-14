"""
Django settings for proj project in production

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
import subprocess
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
apppath =  "%s/pred/app/"%(BASE_DIR)
sys.path.append(apppath)

import myfunc


with open('/etc/django_pro_secret_key.txt') as f:
    SECRET_KEY = f.read().strip()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

try:
    from shared_settings import *
except ImportError:
    pass

