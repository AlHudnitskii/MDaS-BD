from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure--7_9pw6)$g*04h^)s&+_j$za6*%x3iawuc+ies=1y&#gze)_v9'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop.apps.ShopConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'shop.middleware.session.SessionAuthMiddleware',
    'shop.auth.jwt_middleware.JWTAuthMiddleware',
    'shop.middleware.session.CartMiddleware',
]

ROOT_URLCONF = 'shop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'shop.sql_context_processors.auth_context',
                'shop.sql_context_processors.cart_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'shop.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bdshop',
        'USER': 'bdshop',
        'PASSWORD': 'bdshop',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Minsk'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True
CART_SESSION_ID = 'cart'

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = 'redispassword'
REDIS_DB_CACHE = 0
REDIS_DB_SESSIONS = 1
REDIS_DB_PUBSUB = 2

JWT_SECRET_KEY = 'blablablablabla-string'
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
LOGIN_MAX_ATTEMPTS = 3
LOGIN_BLOCK_DURATION = 600


MONGODB_URI = 'mongodb://127.0.0.1:27017/'
MONGODB_USERNAME = None
MONGODB_PASSWORD = None
MONGODB_DATABASE = 'shop_logs'

CACHE_TTL = {
    'users_list': 300,
    'user_roles': 300,
    'product_list': 600,
    'product_detail': 600,
    'categories': 3600,
    'statistics': 1800,
    'analytics': 3600,
    'session': 86400,
}
