from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('mainpage.api_urls')),  # API REST para o app mobile
    path('', include('mainpage.urls')),           # Site web
]


# Serve media files — em produção no Render o Django precisa servir as imagens
# pois não há servidor de mídia separado configurado (ex: S3).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)