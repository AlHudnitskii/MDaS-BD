from django.urls import re_path

from . import views


app_name = 'users'

urlpatterns = [
    re_path(r'^registration/$', views.registration, name='registration'),
    re_path(r'^login/$', views.login, name='login'),
    re_path(r'^profile/$', views.profile, name='profile'),
    re_path(r'^logout/$', views.logout, name='logout'),
]