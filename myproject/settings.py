import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# ------------------------------------------------------------------ #
#  SEGURANÇA — Em produção, mova SECRET_KEY para variável de ambiente  #
# ------------------------------------------------------------------ #
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'chave-local-troque-em-producao-django-insecure-xYz'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')
    if host.strip()
]

# ------------------------------------------------------------------ #
#  APLICAÇÕES                                                          #
# ------------------------------------------------------------------ #
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'storages',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # serve arquivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

# ------------------------------------------------------------------ #
#  BANCO DE DADOS                                                      #
#  PostgreSQL em produção (RDS) — SQLite apenas para testes locais.   #
#  Variáveis injetadas automaticamente pelo Elastic Beanstalk + RDS   #
#  JSONField exige PostgreSQL para suporte nativo a JSONB.             #
# ------------------------------------------------------------------ #
if os.environ.get('RDS_HOSTNAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ.get('RDS_PORT', '5432'),
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }
else:
    # SQLite para testes locais
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ------------------------------------------------------------------ #
#  VALIDAÇÃO DE SENHA                                                  #
# ------------------------------------------------------------------ #
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------ #
#  ARQUIVOS ESTÁTICOS                                                  #
# ------------------------------------------------------------------ #
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# ------------------------------------------------------------------ #
#  ARQUIVOS DE MÍDIA — imagens de produtos                             #
#  Em produção (EB): armazenados no S3                                 #
#  Em desenvolvimento local: armazenados em /media/                    #
# ------------------------------------------------------------------ #
if os.environ.get('AWS_STORAGE_BUCKET_NAME'):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_DEFAULT_ACL = os.environ.get('AWS_DEFAULT_ACL', 'public-read')
    AWS_S3_FILE_OVERWRITE = os.environ.get('AWS_S3_FILE_OVERWRITE', 'False') == 'True'
    MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------------------------------------------ #
#  DRF — sem autenticação para simplificar o lab                       #
# ------------------------------------------------------------------ #
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}
