from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Cart, CartItem, Order, Product, Category
from .services import CheckoutService
from .services.notifications import MockNotificationService


class ProductStockTestCase(TestCase):
    """Pruebas de la lógica de negocio del modelo Product."""

    def setUp(self):
        category = Category.objects.create(name='Test', slug='test')
        self.product = Product.objects.create(
            category=category,
            name='Croquetas Premium',
            slug='croquetas-premium',
            price=Decimal('50.00'),
            stock=10,
        )

    def test_reduce_stock_descuenta_correctamente(self):
        self.product.reduce_stock(3)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)

    def test_is_available_con_stock(self):
        self.assertTrue(self.product.is_available())

    def test_is_available_sin_stock(self):
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.is_available())

    def test_is_available_inactivo(self):
        self.product.is_active = False
        self.product.save()
        self.assertFalse(self.product.is_available())


class CheckoutServiceTestCase(TestCase):
    """Pruebas del servicio de checkout y su integración con inventario."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        category = Category.objects.create(name='Alimentos', slug='alimentos')
        self.product = Product.objects.create(
            category=category,
            name='Alimento para perro',
            slug='alimento-perro',
            price=Decimal('80.00'),
            stock=10,
        )
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)

    def _get_service(self):
        return CheckoutService(notification_service=MockNotificationService())

    def test_checkout_descuenta_stock_correctamente(self):
        """Comprar 3 unidades de stock=10 debe dejar stock en 7."""
        service = self._get_service()
        service.crear_orden_desde_carrito(
            user=self.user,
            cart=self.cart,
            shipping_address='Calle Falsa 123',
            payment_method='efectivo',
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)

    def test_checkout_crea_orden_con_total_correcto(self):
        """El total de la orden debe ser precio × cantidad."""
        service = self._get_service()
        order = service.crear_orden_desde_carrito(
            user=self.user,
            cart=self.cart,
            shipping_address='Calle Falsa 123',
            payment_method='efectivo',
        )
        self.assertEqual(order.total, Decimal('240.00'))  # 80 × 3

    def test_checkout_vacia_el_carrito(self):
        """Después del checkout el carrito debe quedar vacío."""
        service = self._get_service()
        service.crear_orden_desde_carrito(
            user=self.user,
            cart=self.cart,
            shipping_address='Calle Falsa 123',
            payment_method='efectivo',
        )
        self.assertEqual(self.cart.items.count(), 0)

    def test_checkout_falla_si_stock_insuficiente(self):
        """Intentar comprar más del stock disponible debe lanzar ValueError."""
        self.product.stock = 2
        self.product.save()

        service = self._get_service()
        with self.assertRaises(ValueError):
            service.crear_orden_desde_carrito(
                user=self.user,
                cart=self.cart,
                shipping_address='Calle Falsa 123',
                payment_method='efectivo',
            )

    def test_checkout_no_modifica_stock_si_falla(self):
        """Si el checkout falla, el stock no debe haber cambiado (atomicidad)."""
        self.product.stock = 2
        self.product.save()

        service = self._get_service()
        try:
            service.crear_orden_desde_carrito(
                user=self.user,
                cart=self.cart,
                shipping_address='Calle Falsa 123',
                payment_method='efectivo',
            )
        except ValueError:
            pass

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)

    def test_checkout_snapshot_precio_unit_price(self):
        """unit_price en OrderItem debe ser el precio al momento de compra."""
        precio_original = self.product.price
        service = self._get_service()
        order = service.crear_orden_desde_carrito(
            user=self.user,
            cart=self.cart,
            shipping_address='Calle Falsa 123',
            payment_method='efectivo',
        )
        item = order.items.first()
        self.assertEqual(item.unit_price, precio_original)
