from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'compile', views.compile_yaml, name='compile_yaml'),
]
