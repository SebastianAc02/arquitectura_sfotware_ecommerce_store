# Author: Equipo Kibo
# Rutas del PANEL ADMIN: dashboard, CRUD de productos, órdenes

from django.urls import path

from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('productos/', views.product_list, name='product_list'),
    path('productos/nuevo/', views.ProductCreateView.as_view(), name='product_create'),
    path('productos/<int:pk>/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('productos/<int:pk>/del/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('ordenes/', views.order_list, name='order_list'),
]
