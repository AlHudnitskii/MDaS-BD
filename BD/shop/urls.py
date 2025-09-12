from django.contrib import admin
from django.urls import re_path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^cart/', include('cart.urls', namespace='cart')),
    re_path(r'^user/', include('users.urls', namespace='user')),
    re_path(r'^orders/', include('orders.urls', namespace='orders')),
    re_path(r'^', include('main.urls', namespace='main')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                         document_root=settings.MEDIA_ROOT)