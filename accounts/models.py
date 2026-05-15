# Author: Equipo Kibo
# Dominio: AUTH — Autenticacion, roles y perfiles de usuario

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    """
    Extiende el User de Django con campos adicionales.
    Patron: Extension por composicion (OneToOne) en lugar de herencia.
    Nunca modificamos el modelo User de Django directamente — eso es el God User anti-pattern.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    # is_admin controla el rol: True = administrador, False = cliente
    # Las views del admin_panel verifican este campo antes de dar acceso
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Mascota(models.Model):
    """
    Mascota registrada por el usuario.
    Permite recomendaciones basicas por tipo/etapa de vida del animal.
    """
    TIPO_CHOICES = [
        ('perro', _('Perro')),
        ('gato', _('Gato')),
        ('ave', _('Ave')),
        ('otro', _('Otro')),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mascotas')
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    raza = models.CharField(max_length=100, blank=True)
    edad = models.PositiveIntegerField(help_text='Edad en años')
    peso = models.FloatField(help_text='Peso en kg')
    imagen = models.ImageField(
        upload_to='mascotas/',
        blank=True,
        null=True,
        help_text='Foto de tu mascota (opcional)'
    )

    def __str__(self):
        return f"{self.nombre} ({self.tipo}) — {self.user.username}"


# --- SIGNAL: Observer Pattern ---
# Cada vez que se crea un User, automáticamente se crea su UserProfile.
# El User no sabe que existe el Profile — loose coupling.
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
