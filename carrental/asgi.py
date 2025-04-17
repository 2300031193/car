"""
ASGI config for carrental project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carrental.settings')

application = get_asgi_application()
