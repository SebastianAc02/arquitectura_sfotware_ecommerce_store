# Author: Equipo Kibo
from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalogo/', views.catalog_view, name='catalog'),
    path('producto/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('producto/<slug:slug>/wishlist-toggle/', views.wishlist_toggle, name='wishlist_toggle'),
    # Carrito
    path('carrito/', views.cart_view, name='cart'),
    path('carrito/agregar/<slug:slug>/', views.cart_add, name='cart_add'),
    path('carrito/eliminar/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('carrito/actualizar/<int:item_id>/', views.cart_update, name='cart_update'),
    # Checkout
    path('checkout/', views.checkout_view, name='checkout'),
    path('orden/<int:order_id>/confirmacion/', views.order_confirmation, name='order_confirmation'),
    path('mis-ordenes/', views.my_orders, name='my_orders'),
]
