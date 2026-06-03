import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (só tem efeito em desenvolvimento local;
# em produção no EB as variáveis já chegam pelo ambiente do sistema)
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------ #
#  SEGURANÇA — Em produção, mova SECRET_KEY para variável de ambiente  #
# ------------------------------------------------------------------ #
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'chave-local-troque-em-producao-django-insecure-xYz'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']   # simplificado para aula

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
    'corsheaders',
    'storages',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # serve arquivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
       "https://example.com",
       "https://sub.example.com",
       "http://localhost:3001",  # Exemplo para um app local
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
#  PostgreSQL em todos os ambientes.                                   #
#  - Local: variáveis lidas do arquivo .env                            #
#  - Produção (EB): variáveis RDS_* injetadas pelo Elastic Beanstalk   #
#  JSONField exige PostgreSQL para suporte nativo a JSONB.             #
# ------------------------------------------------------------------ #
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     os.environ.get('RDS_DB_NAME',   'produtos_db'),
        'USER':     os.environ.get('RDS_USERNAME',  'postgres'),
        'PASSWORD': os.environ.get('RDS_PASSWORD',  'postgres'),
        'HOST':     os.environ.get('RDS_HOSTNAME',  'localhost'),
        'PORT':     os.environ.get('RDS_PORT',      '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
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
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_FILE_OVERWRITE = False
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
