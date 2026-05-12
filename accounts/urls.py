# Author: Equipo Kibo
# Rutas del dominio AUTH: login, logout, registro, perfil, mascotas

from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    # Mascotas
    path('mascotas/', views.mascota_list, name='mascota_list'),
    path('mascotas/agregar/', views.mascota_create, name='mascota_create'),
    path('mascotas/<int:pk>/editar/', views.mascota_edit, name='mascota_edit'),
    path('mascotas/<int:pk>/eliminar/', views.mascota_delete, name='mascota_delete'),
]
