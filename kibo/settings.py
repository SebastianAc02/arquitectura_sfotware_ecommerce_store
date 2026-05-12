# Author: Equipo Kibo
# Configuracion principal del proyecto Django — Kibo Pet E-commerce
# Usa python-decouple para leer variables sensibles del archivo .env

from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURIDAD ---
# SECRET_KEY viene del .env — nunca hardcodeada en codigo
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = ['*']

# --- APPS INSTALADAS ---
# Django necesita saber que apps existen para migrar modelos y encontrar templates
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps del proyecto Kibo
    'accounts',      # Autenticacion, roles, perfiles, mascotas
    'store',         # Catalogo, carrito, checkout, reviews, wishlist
    'admin_panel',   # Panel de administracion custom (NO es el Django admin)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # LocaleMiddleware debe ir después de SessionMiddleware y antes de CommonMiddleware
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kibo.urls'

# --- TEMPLATES ---
# DIRS incluye la carpeta global de templates (base_public.html, base_admin.html)
# APP_DIRS=True hace que Django tambien busque en templates/ dentro de cada app
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Inyecta cart_count en todos los templates sin pasarlo por cada view
                'store.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'kibo.wsgi.application'

# --- BASE DE DATOS ---
# PostgreSQL corre en el contenedor 'db' de Docker Compose
# El HOST es 'db' porque ese es el nombre del servicio en docker-compose.yml
# Todos los valores vienen del .env — nunca hardcodeados
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNACIONALIZACION ---
# Soporte para Español e Inglés (i18n requerido por la rúbrica de Entrega 2)
LANGUAGE_CODE = 'es'
LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTATICOS (CSS, JS, imagenes del sistema) ---
# STATIC_URL: ruta publica para acceder a los archivos estaticos
# STATICFILES_DIRS: carpetas donde Django los busca en desarrollo
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# --- ARCHIVOS DE MEDIA (uploads del usuario: fotos de productos) ---
# MEDIA_URL: ruta publica para acceder a uploads
# MEDIA_ROOT: carpeta fisica donde se guardan los archivos subidos
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- AUTENTICACION ---
# LOGIN_URL: a donde redirige cuando una view requiere login
# LOGIN_REDIRECT_URL: a donde va el usuario despues de hacer login
# LOGOUT_REDIRECT_URL: a donde va despues de hacer logout
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
