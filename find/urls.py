from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Importa o arquivo que você mandou
from django.conf.urls.static import static # Importa a função de arquivos estáticos

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mainpage.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)