import os
from django.core.wsgi import get_wsgi_application

from dotenv import load_dotenv
load_dotenv()  # carrega o .env em desenvolvimento local

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_wsgi_application()
