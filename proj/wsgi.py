"""
WSGI config for proj project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys
import site

rundir = os.path.dirname(os.path.abspath(__file__))
basedir = os.path.abspath("%s/../"%(rundir))
path_log = "%s/pred/static/log"%(rundir)


# Activate the virtual env
activate_env="%s/env/bin/activate_this.py"%(basedir)
exec(compile(open(activate_env, "r").read(), activate_env, 'exec'), dict(__file__=activate_env))


#Add the site-packages of the virtualenv

# Add the directory for the project
sys.path.append(basedir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
