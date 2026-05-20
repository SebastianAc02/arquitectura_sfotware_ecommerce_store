# Author: Equipo Kibo
# Formularios del dominio AUTH

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Mascota, UserProfile


class RegisterForm(UserCreationForm):
    """Registro de usuario final con email opcional."""

    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserUpdateForm(forms.ModelForm):
    """Actualización de datos básicos del usuario."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class ProfileUpdateForm(forms.ModelForm):
    """Actualización de datos extendidos del perfil."""

    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'pais']


class _CaseInsensitiveChoiceField(forms.ChoiceField):
    """ChoiceField que normaliza el valor a minúsculas antes de validar."""
    def to_python(self, value):
        value = super().to_python(value)
        return value.lower().strip() if value else value


class MascotaForm(forms.ModelForm):
    """Formulario para registrar o editar una mascota del usuario."""

    # Campo explícito para que la normalización ocurra antes de la validación
    tipo = _CaseInsensitiveChoiceField(
        choices=Mascota.TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
    )

    class Meta:
        model = Mascota
        fields = ['nombre', 'tipo', 'raza', 'edad', 'peso', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'raza': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'list': 'razas-list',
                'autocomplete': 'off',
                'placeholder': 'Escribe o selecciona una raza...',
            }),
            'edad': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': 0}),
            'peso': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': 0, 'step': '0.1'}),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/png, image/jpeg, image/webp',
            }),
        }
