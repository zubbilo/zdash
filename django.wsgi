import os, sys, site

sys.path.append('/var/www/zdash')

os.environ['DJANGO_SETTINGS_MODULE'] = 'zdash.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
