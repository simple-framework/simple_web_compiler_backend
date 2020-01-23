from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^yaml/', include('simple_yaml_compiler_backend.apps.yaml_compiler.urls')),
]
