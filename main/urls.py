from django.urls import re_path
from . import views


app_name = 'main'

urlpatterns = [
    re_path(r'^$', views.popular_list, name='popular_list'),
    re_path(r'^shop/$', views.product_list, name='product_list'),
    re_path(r'^shop/(?P<slug>[\w-]+)/$', views.product_detail, name='product_detail'),
    re_path(r'^shop/category/(?P<category_slug>[\w-]+)/$', views.product_list, name='product_list_by_category'),
    re_path(r'^about/$', views.about, name='about'),
    re_path(r'^news/$', views.news, name='news'),
    re_path(r'^dict/$', views.dict, name='dict'),
    re_path(r'^contacts/$', views.contacts, name='contacts'),
    re_path(r'^vacancies/$', views.vacancies, name='vacancies'),
    re_path(r'^promocodes/$', views.promocodes, name='promocodes'),
    re_path(r'^reviews/$', views.reviews, name='reviews'),
    re_path(r'^statistics/$', views.statistics, name='statistics'),
]