# Author: Equipo Kibo
# Context processor: inyecta cart_count en TODOS los templates automaticamente.
# Registrado en settings.py -> TEMPLATES -> OPTIONS -> context_processors.
# Evita pasar el conteo del carrito manualmente en cada view (DRY).


def cart_count(request):
    """Retorna cart_count y cart_total del usuario autenticado."""
    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            return {
                'cart_count': cart.get_item_count(),
                'cart_total': cart.get_total(),
            }
        except Exception:
            return {'cart_count': 0, 'cart_total': 0}
    return {'cart_count': 0, 'cart_total': 0}
