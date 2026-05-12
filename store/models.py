# Author: Equipo Kibo
# Dominio: CATALOGO, CARRITO, CHECKOUT — Tienda publica

from decimal import Decimal, InvalidOperation

from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """
    Categoria de productos (Alimentos, Juguetes, Accesorios...).
    Slug permite URLs limpias: /catalogo/alimentos/ en vez de /catalogo/1/
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(is_active=True)

    def top_vendidos(self):
        return self.annotate(
            sold_qty=Coalesce(Sum('orderitem__quantity'), 0)
        ).order_by('-sold_qty', '-created_at')

    def filter_by(self, params):
        qs = self

        category_slug = (params.get('categoria') or '').strip()
        tipo = (params.get('tipo') or '').strip().lower()
        precio_min_raw = (params.get('precio_min') or '').strip()
        precio_max_raw = (params.get('precio_max') or '').strip()

        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        if tipo:
            qs = qs.filter(tipo_mascota__iexact=tipo)

        if precio_min_raw:
            try:
                precio_min = Decimal(precio_min_raw)
                qs = qs.filter(price__gte=precio_min)
            except InvalidOperation:
                pass

        if precio_max_raw:
            try:
                precio_max = Decimal(precio_max_raw)
                qs = qs.filter(price__lte=precio_max)
            except InvalidOperation:
                pass

        return qs


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def activos(self):
        return self.get_queryset().activos()

    def top_vendidos(self):
        return self.get_queryset().top_vendidos()

    def filter_by(self, params):
        return self.get_queryset().filter_by(params)


class Product(models.Model):
    """
    Producto del catalogo.
    Patron Fat Model: la logica del negocio (disponibilidad, reduccion de stock)
    vive aqui — no en las views.
    """
    objects = ProductManager()

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    # Campos para recomendaciones basicas por perfil de mascota
    tipo_mascota = models.CharField(max_length=50, blank=True,
                                    help_text='perro, gato, ave, todos')
    etapa_vida = models.CharField(max_length=50, blank=True,
                                   help_text='cachorro, adulto, senior, todos')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['tipo_mascota', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def is_available(self):
        """Verifica si el producto esta activo y tiene stock."""
        return self.is_active and self.stock > 0

    def reduce_stock(self, qty):
        """
        Reduce el stock tras una compra.
        Se llama dentro de transaction.atomic() en el checkout
        para evitar race conditions.
        """
        self.stock -= qty
        self.save()


class Cart(models.Model):
    """
    Carrito de compras — estado temporal del usuario.
    Se destruye (vacia) al hacer checkout.
    Cada usuario tiene UN solo carrito (OneToOne via user).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.user.username}"

    def get_total(self):
        """
        Patron Fat Model: el total se calcula aqui, no en la view.
        Suma los subtotales de todos los CartItems.
        """
        return sum(item.get_subtotal() for item in self.items.all())

    def get_item_count(self):
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        """Vacia el carrito despues del checkout."""
        self.items.all().delete()


class CartItem(models.Model):
    """Item dentro del carrito. Relaciona un producto con una cantidad."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def get_subtotal(self):
        return self.product.price * self.quantity


class Order(models.Model):
    """
    Orden de compra — registro permanente de una transaccion.
    Maquina de estados (FSM): solo ciertas transiciones son validas.
    pending -> confirmed -> shipped -> delivered (o cancelled).
    Usar choices evita strings libres inconsistentes en la DB.
    """
    STATUS_CHOICES = [
        ('pending',   _('Pendiente')),
        ('confirmed', _('Confirmado')),
        ('shipped',   _('Enviado')),
        ('delivered', _('Entregado')),
        ('cancelled', _('Cancelado')),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField()
    payment_method = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Orden #{self.id} — {self.user.username} — {self.status}"

    def calculate_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def cancel(self):
        self.status = 'cancelled'
        self.save()


class OrderItem(models.Model):
    """
    Item dentro de una orden.
    IMPORTANTE: unit_price guarda el precio EN EL MOMENTO de la compra (Snapshot Pattern).
    Si el precio del producto cambia despues, la factura historica NO se altera.
    Por esto NO referenciamos product.price — copiamos el valor.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} @ {self.unit_price}"

    def get_subtotal(self):
        return self.unit_price * self.quantity


class Review(models.Model):
    """
    Resena de un producto por un usuario.
    unique_together garantiza que un usuario no pueda dejar dos reviews
    para el mismo producto — enforzado a nivel de base de datos.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text='Calificacion del 1 al 5'
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review de {self.user.username} en {self.product.name} ({self.rating}/5)"


class Wishlist(models.Model):
    """
    Lista de favoritos del usuario.
    Funcionalidad especial #1: boton de favorito/wishlist.
    unique_together evita duplicados: un producto no puede estar
    dos veces en la wishlist del mismo usuario.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} — {self.product.name}"
