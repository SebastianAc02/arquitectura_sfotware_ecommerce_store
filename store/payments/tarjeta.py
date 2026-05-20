from decimal import Decimal

from .base import MetodoPago


class PagoTarjeta(MetodoPago):
    """
    Implementación 1: pago con saldo virtual.
    Descuenta el monto del saldo ficticio almacenado en UserProfile.saldo.
    """

    def __init__(self, user):
        self.user = user

    def procesar_pago(self, orden):
        profile = self.user.profile
        if profile.saldo < orden.total:
            raise ValueError(
                f'Saldo insuficiente. Disponible: ${profile.saldo:.2f}, requerido: ${orden.total}'
            )
        profile.saldo -= Decimal(str(orden.total))
        profile.save()
        return {'saldo_restante': profile.saldo}
