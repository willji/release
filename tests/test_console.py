import os
import sys

PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, os.pardir))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
