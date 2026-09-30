"""
============================================================
CONFIGURACIÓN PRINCIPAL DEL PROYECTO
Proyecto: Tienda de Hardware y Componentes PC (Retail)
Asignatura: Desarrollo Backend
============================================================
Este archivo centraliza la configuración de Django:
- Rutas base y seguridad
- Aplicaciones instaladas
- Middleware
- Base de datos PostgreSQL
- Autenticación JWT
- Documentación OpenAPI
- Archivos estáticos y media
============================================================
"""

from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

# ============================================================
# RUTAS BASE
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# SEGURIDAD
# ============================================================
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ============================================================
# APLICACIONES INSTALADAS
# ============================================================
INSTALLED_APPS = [
    # --- Django por defecto ---
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # --- Terceros ---
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # Para logout real
    'django_filters',
    'drf_spectacular',
    'corsheaders',

    # --- Apps del proyecto ---
    'apps.users',
    'apps.catalog',
    'apps.cart',
    'apps.orders',
]

# ============================================================
# MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',      # CORS primero
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ============================================================
# TEMPLATES (Frontend HTML)
# ============================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # Carpeta global de templates
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

WSGI_APPLICATION = 'config.wsgi.application'

# ============================================================
# BASE DE DATOS - PostgreSQL (OBLIGATORIO por la evaluación)
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',   # ← Fuerza UTF-8 en la conexión
        },
    }
}

# ============================================================
# VALIDACIÓN DE CONTRASEÑAS
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================
# INTERNACIONALIZACIÓN
# ============================================================
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# ============================================================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ============================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'   # Para collectstatic

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================
# MODELO DE USUARIO PERSONALIZADO
# ============================================================
AUTH_USER_MODEL = 'users.User'

# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================
REST_FRAMEWORK = {
    # Autenticación por defecto: JWT
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Permisos por defecto: solo lectura pública, escritura autenticada
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    # Filtros globales
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    # Paginación
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    # Esquema OpenAPI (Swagger)
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ============================================================
# JWT - Simple JWT
# ============================================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_LIFETIME_MINUTES', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('JWT_REFRESH_LIFETIME_DAYS', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# ============================================================
# DRF SPECTACULAR (Swagger / OpenAPI)
# ============================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'API Tienda de Hardware y Componentes PC',
    'DESCRIPTION': (
        '## Descripción General\n\n'
        'API REST para e-commerce de componentes informáticos desarrollada '
        'con Django REST Framework y PostgreSQL.\n\n'
        '## Características principales\n\n'
        '- 🔐 Autenticación JWT con claims de rol (CLIENTE / ADMIN)\n'
        '- 🛒 Carro de compras persistente (relación 1:1 con usuario)\n'
        '- 📦 Control transaccional de stock con `select_for_update`\n'
        '- 🔍 Filtros avanzados con `django-filter`\n'
        '- 📝 Documentación OpenAPI automática\n\n'
        '## Autenticación\n\n'
        '1. Hacer login en `POST /api/auth/login/`\n'
        '2. Copiar el `access` token\n'
        '3. Hacer clic en **Authorize** y pegar `Bearer <access>`\n'
        '4. Los endpoints protegidos ya estarán disponibles\n\n'
        '## Roles y permisos\n\n'
        '- **Público**: lectura de catálogo\n'
        '- **Cliente**: gestión de carro, checkout y pago de sus órdenes\n'
        '- **Administrador**: gestión de catálogo, inventario y estados de órdenes'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,

    # --- Configuración de la UI de Swagger ---
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,      # Mantiene el token entre recargas
        'displayOperationId': False,
        'filter': True,                    # Habilita búsqueda de endpoints
        'defaultModelsExpandDepth': 2,
    },

    # --- Agrupación por tags ---
    'TAGS': [
        {'name': 'Autenticación', 'description': 'Registro, login, logout y perfil.'},
        {'name': 'Catálogo - Categorías', 'description': 'CRUD de categorías.'},
        {'name': 'Catálogo - Marcas', 'description': 'CRUD de marcas.'},
        {'name': 'Catálogo - Productos', 'description': 'CRUD de productos con filtros.'},
        {'name': 'Carro de Compras', 'description': 'Gestión del carro persistente.'},
        {'name': 'Órdenes', 'description': 'Checkout, pago, cancelación y estados.'},
    ],

    # --- Orden de los tags en la UI ---
    'TAGS_SORTER': 'alpha',

    # --- Servidores ---
    'SERVERS': [
        {'url': 'http://127.0.0.1:8000', 'description': 'Servidor de desarrollo'},
    ],
}

# ============================================================
# CORS (para que el frontend pueda consumir la API)
# ============================================================
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
CORS_ALLOW_CREDENTIALS = True

# ============================================================
# CLAVE PRIMARIA POR DEFECTO
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# LOGGING
# ============================================================
# Configuración de logging para mostrar las señales en consola.
# Los mensajes INFO de nuestras señales se verán con formato legible.
# ============================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{levelname}] {asctime} - {message}',
            'style': '{',
            'datefmt': '%H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}