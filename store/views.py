# Author: Equipo Kibo
import requests as http_client

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView

from .models import Cart, CartItem, Category, Order, OrderItem, Product, Review, Wishlist
from .payments import PagoCheque, PagoTarjeta
from .services import CheckoutService

PAYMENT_CHOICES = [
    ('tarjeta', _('Tarjeta virtual (descuenta saldo)')),
    ('cheque',  _('Cheque (descarga PDF comprobante)')),
]


def home(request):
    """Vista principal de la tienda — página de inicio."""
    from .services.recomendaciones import recomendar_para_mascota

    products = Product.objects.activos().select_related('category')[:8]
    categories = Category.objects.all()

    recomendaciones_por_mascota = []
    if request.user.is_authenticated:
        for mascota in request.user.mascotas.all():
            recomendaciones_por_mascota.append({
                'mascota': mascota,
                'productos': recomendar_para_mascota(mascota, n=6),
            })

    return render(request, 'store/home.html', {
        'products': products,
        'categories': categories,
        'recomendaciones_por_mascota': recomendaciones_por_mascota,
    })


def catalog_view(request):
    """Listado de productos con filtros por GET params y paginación."""
    products_qs = (
        Product.objects.activos()
        .select_related('category')
        .filter_by(request.GET)
    )
    categories = Category.objects.all()

    top_vendidos = Product.objects.activos().top_vendidos()[:6]
    top_ids = [p.id for p in top_vendidos if getattr(p, 'sold_qty', 0) > 0]

    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = set(
            Wishlist.objects.filter(user=request.user, product__in=products_qs)
            .values_list('product_id', flat=True)
        )

    context = {
        'products': products,
        'categories': categories,
        'wishlist_ids': wishlist_ids,
        'top_ids': top_ids,
        'selected_categoria': request.GET.get('categoria', ''),
        'selected_tipo': request.GET.get('tipo', ''),
        'selected_precio_min': request.GET.get('precio_min', ''),
        'selected_precio_max': request.GET.get('precio_max', ''),
    }
    return render(request, 'store/catalog.html', context)


class ProductDetailView(DetailView):
    """
    Detalle de producto usando DetailView — CBV genérica extensible por herencia.
    Patrón: en lugar de copiar la función, se subclasea esta vista para variantes.
    """
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.activos().select_related('category')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.object

        reviews = Review.objects.filter(product=product).select_related('user')

        recommendation_qs = Product.objects.activos().filter(
            category=product.category,
        ).exclude(id=product.id)

        if product.tipo_mascota:
            recommendation_qs = recommendation_qs.filter(tipo_mascota__iexact=product.tipo_mascota)

        recommendations = list(recommendation_qs.select_related('category')[:4])
        if len(recommendations) < 4:
            current_ids = [p.id for p in recommendations]
            fill = Product.objects.activos().filter(
                category=product.category,
            ).exclude(id__in=[product.id, *current_ids]).select_related('category')[: (4 - len(recommendations))]
            recommendations.extend(list(fill))

        is_wishlisted = False
        wishlist_reco_ids = set()
        if self.request.user.is_authenticated:
            is_wishlisted = Wishlist.objects.filter(
                user=self.request.user, product=product
            ).exists()
            wishlist_reco_ids = set(
                Wishlist.objects.filter(
                    user=self.request.user, product__in=recommendations
                ).values_list('product_id', flat=True)
            )

        ctx.update({
            'reviews': reviews,
            'recommendations': recommendations,
            'is_wishlisted': is_wishlisted,
            'wishlist_reco_ids': wishlist_reco_ids,
        })
        return ctx


@login_required
def wishlist_toggle(request, slug):
    """Toggle de wishlist usando PRG: POST -> redirect."""
    product = get_object_or_404(Product, slug=slug, is_active=True)

    favorite, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, _('"%s" agregado a tu wishlist.') % product.name)
    else:
        favorite.delete()
        messages.info(request, _('"%s" removido de tu wishlist.') % product.name)

    next_url = request.POST.get('next') or request.GET.get('next')
    if not next_url:
        next_url = request.META.get('HTTP_REFERER')
    if not next_url:
        next_url = reverse('store:product_detail', kwargs={'slug': product.slug})

    return redirect(next_url)


# ─────────────────────────────────────────────
# CARRITO
# ─────────────────────────────────────────────

@login_required
def cart_preview(request):
    """JSON con items del carrito para el panel lateral del navbar."""
    cart, _cr = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product').all()
    data = []
    for item in items:
        data.append({
            'id':        item.id,
            'name':      item.product.name,
            'quantity':  item.quantity,
            'subtotal':  str(item.product.price * item.quantity),
            'image_url': (
                request.build_absolute_uri(item.product.image.url)
                if item.product.image else None
            ),
            'slug': item.product.slug,
        })
    return JsonResponse({
        'items': data,
        'total': str(cart.get_total()),
        'count': cart.get_item_count(),
    })


@login_required
def cart_view(request):
    """Muestra el carrito del usuario con items y total."""
    cart, _cr = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product__category').all()
    return render(request, 'store/cart.html', {
        'cart': cart,
        'items': items,
    })


@login_required
def cart_add(request, slug):
    """POST: agrega un producto al carrito o incrementa su cantidad. PRG."""
    if request.method != 'POST':
        return redirect('store:catalog')

    product = get_object_or_404(Product, slug=slug, is_active=True)

    if not product.is_available():
        messages.warning(request, _('"%s" no tiene stock disponible.') % product.name)
        return redirect('store:product_detail', slug=slug)

    cart, _cr = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()

    messages.success(request, _('"%s" agregado al carrito.') % product.name)
    return redirect('store:product_detail', slug=slug)


@login_required
def cart_remove(request, item_id):
    """POST: elimina un CartItem del carrito."""
    if request.method != 'POST':
        return redirect('store:cart')
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, _('Producto eliminado del carrito.'))
    return redirect('store:cart')


@login_required
def cart_update(request, item_id):
    """POST: actualiza la cantidad de un CartItem."""
    if request.method != 'POST':
        return redirect('store:cart')
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    try:
        qty = int(request.POST.get('quantity', 1))
    except ValueError:
        qty = 1
    if qty < 1:
        item.delete()
        messages.info(request, _('Producto eliminado del carrito.'))
    else:
        item.quantity = qty
        item.save()
    return redirect('store:cart')


# ─────────────────────────────────────────────
# CHECKOUT — delega lógica de negocio a CheckoutService
# ─────────────────────────────────────────────

@login_required
def checkout_view(request):
    """
    GET:  muestra formulario de dirección y método de pago.
    POST: valida inputs HTTP y delega la lógica transaccional a CheckoutService.
    La vista sólo maneja HTTP; el servicio maneja negocio (separación de capas).
    """
    cart, _cr = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product').all()

    if not items.exists():
        messages.warning(request, _('Tu carrito está vacío.'))
        return redirect('store:cart')

    try:
        saldo = request.user.profile.saldo
    except Exception:
        saldo = 0

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address', '').strip()
        payment_method = request.POST.get('payment_method', '')

        ctx_error = {'cart': cart, 'items': items, 'payment_choices': PAYMENT_CHOICES, 'saldo': saldo}

        if not shipping_address:
            messages.error(request, _('La dirección de envío es obligatoria.'))
            return render(request, 'store/checkout.html', ctx_error)

        if payment_method not in dict(PAYMENT_CHOICES):
            messages.error(request, _('Método de pago no válido.'))
            return render(request, 'store/checkout.html', ctx_error)

        # DI: instanciar método de pago concreto según elección del usuario
        if payment_method == 'tarjeta':
            metodo_pago = PagoTarjeta(request.user)
            if saldo < cart.get_total():
                messages.error(
                    request,
                    _('Saldo insuficiente. Tu saldo virtual: $%(s)s') % {'s': f'{saldo:.2f}'},
                )
                return render(request, 'store/checkout.html', ctx_error)
        else:
            metodo_pago = PagoCheque()

        try:
            service = CheckoutService()
            order = service.crear_orden_desde_carrito(
                user=request.user,
                cart=cart,
                shipping_address=shipping_address,
                payment_method=payment_method,
            )
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'store/checkout.html', ctx_error)

        # Procesar pago con la interfaz abstracta (DI en acción)
        resultado = metodo_pago.procesar_pago(order)

        if payment_method == 'cheque':
            response = HttpResponse(resultado.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="cheque_orden_{order.id}.pdf"'
            return response

        # tarjeta: mostrar saldo restante y redirigir
        messages.success(
            request,
            _('¡Orden creada! Saldo restante: $%(s)s') % {'s': resultado['saldo_restante']},
        )
        return redirect('store:order_confirmation', order_id=order.id)

    return render(request, 'store/checkout.html', {
        'cart': cart,
        'items': items,
        'payment_choices': PAYMENT_CHOICES,
        'saldo': saldo,
    })


@login_required
def order_confirmation(request, order_id):
    """Página de confirmación post-checkout."""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        id=order_id,
        user=request.user,
    )
    return render(request, 'store/order_confirmation.html', {'order': order})


@login_required
def my_orders(request):
    """Historial de órdenes del usuario autenticado con paginación."""
    orders_qs = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related('items__product')
        .order_by('-created_at')
    )
    paginator = Paginator(orders_qs, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    return render(request, 'store/my_orders.html', {'orders': orders})


# ─────────────────────────────────────────────
# RAZAS — TheDogAPI
# ─────────────────────────────────────────────

def razas_view(request):
    """
    GET /razas/
    Muestra tarjetas de razas de perros usando TheDogAPI.
    La respuesta se cachea en sesión para evitar múltiples llamadas.
    """
    razas = request.session.get('thedogapi_breeds')
    if not razas:
        try:
            resp = http_client.get(
                'https://api.thedogapi.com/v1/breeds',
                params={'limit': 12},
                timeout=5,
            )
            if resp.ok:
                razas = resp.json()[:12]
                request.session['thedogapi_breeds'] = razas
            else:
                razas = []
        except Exception:
            razas = []
    return render(request, 'store/razas.html', {'razas': razas})


# ─────────────────────────────────────────────
# API JSON PÚBLICA
# ─────────────────────────────────────────────

def productos_api(request):
    """
    GET /api/productos/
    Retorna productos activos con stock > 0 en formato JSON.
    Público — no requiere autenticación.
    """
    products = (
        Product.objects
        .activos()
        .filter(stock__gt=0)
        .select_related('category')
        .order_by('name')
    )

    data = []
    for p in products:
        imagen_url = (
            request.build_absolute_uri(p.image.url) if p.image else None
        )
        detalle_url = request.build_absolute_uri(
            reverse('store:product_detail', kwargs={'slug': p.slug})
        )
        data.append({
            'id':          p.id,
            'nombre':      p.name,
            'precio':      str(p.price),
            'categoria':   p.category.name,
            'stock':       p.stock,
            'imagen_url':  imagen_url,
            'detalle_url': detalle_url,
        })

    return JsonResponse({'productos': data})
