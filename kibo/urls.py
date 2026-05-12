# Author: Equipo Kibo
# Router principal — delega a cada app con include()
# Patron Facade: una sola entrada que distribuye el trabajo

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin built-in (distinto del admin_panel custom)
    path('django-admin/', admin.site.urls),

    # i18n: selector de idioma (/i18n/setlang/)
    path('i18n/', include('django.conf.urls.i18n')),

    # App: accounts — login, logout, registro, perfil, mascotas
    path('accounts/', include('accounts.urls')),

    # App: store — catalogo, carrito, checkout (raiz del sitio)
    path('', include('store.urls')),

    # App: admin_panel — panel de administracion custom
    path('panel/', include('admin_panel.urls')),
]

# En desarrollo, Django sirve los archivos de media directamente
# En produccion (AWS), Nginx o S3 se encargaria de esto
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
