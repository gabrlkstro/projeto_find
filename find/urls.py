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

from django.views.static import serve
from django.urls import re_path

# Serve media files em produção (Render)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
