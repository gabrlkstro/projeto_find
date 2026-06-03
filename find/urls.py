from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API REST (cada app tem suas próprias rotas)
    path('api/', include('accounts.api.urls')),
    path('api/', include('items.api.urls')),
    path('api/', include('chats.api.urls')),

    # Site web
    path('', include('mainpage.urls')),
]

# Serve media files em produção (Render)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
