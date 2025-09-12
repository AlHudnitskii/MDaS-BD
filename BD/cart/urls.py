from django.urls import path, re_path
from . import views


app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    re_path(r'^add/(?P<product_id>\d+)/$', views.cart_add, name='cart_add'),
    re_path(r'^remove/(?P<product_id>\d+)/$', views.cart_remove, name='cart_remove'),
    path('update/<int:product_id>/', views.cart_update, name='cart_update'),

]
