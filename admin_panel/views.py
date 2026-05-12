# Author: Equipo Kibo
# Vistas del PANEL ADMIN custom

import functools

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import ProductForm
from store.models import Order, Product


def _is_admin_user(user):
    profile = getattr(user, 'profile', None)
    return bool(user.is_authenticated and profile and profile.is_admin)


def admin_required(view_func):
    """Decorator para FBVs que requieren profile.is_admin=True.
    functools.wraps preserva el nombre de la view para que {% url %} funcione.
    """
    @login_required
    @functools.wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not _is_admin_user(request.user):
            return HttpResponseForbidden(_('No tienes permisos para acceder al panel administrativo.'))
        return view_func(request, *args, **kwargs)
    return _wrapped


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin reutilizable para CBVs que requieren rol de administrador.
    Sustituye al decorador @admin_required en vistas basadas en clases.
    Patrón: herencia de mixin — una sola pieza de control de acceso extensible.
    """

    def dispatch(self, request, *args, **kwargs):
        if not _is_admin_user(request.user):
            return HttpResponseForbidden(_('No tienes permisos para acceder al panel administrativo.'))
        return super().dispatch(request, *args, **kwargs)


# ─────────────────────────────────────────────
# FBVs con lógica de consulta compleja
# ─────────────────────────────────────────────

@admin_required
def dashboard(request):
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    total_sales = Order.objects.exclude(status='cancelled').aggregate(total=Sum('total'))['total'] or 0

    top_products = (
        Product.objects.annotate(sold_qty=Sum('orderitem__quantity'))
        .order_by('-sold_qty')[:5]
    )

    top_commented = (
        Product.objects.annotate(review_count=Count('reviews'))
        .order_by('-review_count')[:5]
    )

    return render(
        request,
        'admin_panel/dashboard.html',
        {
            'total_products': total_products,
            'active_products': active_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_sales': total_sales,
            'top_products': top_products,
            'top_commented': top_commented,
        },
    )


@admin_required
def product_list(request):
    products = Product.objects.select_related('category').all()
    return render(request, 'admin_panel/product_list.html', {'products': products})


@admin_required
def order_list(request):
    orders = Order.objects.select_related('user').prefetch_related('items__product').all()
    return render(request, 'admin_panel/order_list.html', {'orders': orders})


# ─────────────────────────────────────────────
# CBVs para CRUD de productos (extensibles por herencia)
# ─────────────────────────────────────────────

class ProductCreateView(AdminRequiredMixin, CreateView):
    """Creación de producto usando CreateView — reemplaza el if request.method=='POST' manual."""
    model = Product
    form_class = ProductForm
    template_name = 'admin_panel/product_form.html'
    success_url = reverse_lazy('admin_panel:product_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['mode'] = 'create'
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _('Producto creado correctamente.'))
        return super().form_valid(form)


class ProductUpdateView(AdminRequiredMixin, UpdateView):
    """Edición de producto usando UpdateView — hereda lógica HTTP automáticamente."""
    model = Product
    form_class = ProductForm
    template_name = 'admin_panel/product_form.html'
    success_url = reverse_lazy('admin_panel:product_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['mode'] = 'edit'
        ctx['product'] = self.object
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _('Producto actualizado correctamente.'))
        return super().form_valid(form)


class ProductDeleteView(AdminRequiredMixin, DeleteView):
    """Eliminación de producto usando DeleteView."""
    model = Product
    template_name = 'admin_panel/product_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:product_list')
    context_object_name = 'product'

    def form_valid(self, form):
        messages.success(self.request, _('Producto eliminado correctamente.'))
        return super().form_valid(form)
