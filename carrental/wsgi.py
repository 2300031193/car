"""
WSGI config for carrental project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carrental.settings')

application = get_wsgi_application()
