from django.db import transaction

from store.models import Cart, Order, OrderItem
from .notifications import NotificationService, EmailNotificationService


class CheckoutService:
    """
    Capa de servicio: extrae la lógica de negocio del checkout fuera de la vista.
    Depende de NotificationService (abstracción), no de la implementación concreta (DIP).
    """

    def __init__(self, notification_service: NotificationService = None):
        self.notification_service = notification_service or EmailNotificationService()

    @transaction.atomic
    def crear_orden_desde_carrito(
        self,
        user,
        cart: Cart,
        shipping_address: str,
        payment_method: str,
    ) -> Order:
        items = list(cart.items.select_related('product').all())
        self._validar_stock(items)
        order = self._crear_orden(user, cart, shipping_address, payment_method)
        self._crear_order_items(order, items)
        self._reducir_inventario(items)
        cart.clear()
        self.notification_service.notify_order_confirmed(order)
        return order

    def _validar_stock(self, items) -> None:
        for item in items:
            if item.product.stock < item.quantity:
                raise ValueError(
                    f'Stock insuficiente para "{item.product.name}". '
                    f'Disponible: {item.product.stock}, solicitado: {item.quantity}.'
                )

    def _crear_orden(self, user, cart, shipping_address, payment_method) -> Order:
        return Order.objects.create(
            user=user,
            total=cart.get_total(),
            shipping_address=shipping_address,
            payment_method=payment_method,
            status='pending',
        )

    def _crear_order_items(self, order, items) -> None:
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.product.price,  # Snapshot Pattern
            )

    def _reducir_inventario(self, items) -> None:
        for item in items:
            item.product.reduce_stock(item.quantity)
