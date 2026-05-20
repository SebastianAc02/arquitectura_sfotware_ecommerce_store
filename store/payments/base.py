from abc import ABC, abstractmethod


class MetodoPago(ABC):
    """
    Interfaz abstracta para métodos de pago.
    Patrón: Inversión de Dependencias — el checkout depende de esta abstracción,
    no de PagoTarjeta o PagoCheque directamente.
    """

    @abstractmethod
    def procesar_pago(self, orden):
        """Procesa el pago de la orden y retorna el resultado específico de cada implementación."""
        ...
