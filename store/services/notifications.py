from abc import ABC, abstractmethod

from django.core.mail import send_mail


class NotificationService(ABC):
    """Interfaz abstracta para notificaciones de órdenes (Principio DIP)."""

    @abstractmethod
    def notify_order_confirmed(self, order) -> None: ...


class EmailNotificationService(NotificationService):
    """Envía confirmación de orden por correo electrónico."""

    def notify_order_confirmed(self, order) -> None:
        send_mail(
            subject=f'Orden #{order.id} confirmada — Kibo',
            message=(
                f'Hola {order.user.username},\n\n'
                f'Tu orden #{order.id} por ${order.total} ha sido recibida.\n'
                f'Método de pago: {order.payment_method}\n'
                f'Dirección: {order.shipping_address}\n\n'
                f'Gracias por comprar en Kibo!'
            ),
            from_email='noreply@kibo.com',
            recipient_list=[order.user.email],
            fail_silently=True,
        )


class MockNotificationService(NotificationService):
    """Implementación no-op para pruebas (evita enviar correos reales)."""

    def __init__(self):
        self.sent = []

    def notify_order_confirmed(self, order) -> None:
        self.sent.append(order)
