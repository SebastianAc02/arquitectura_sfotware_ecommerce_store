# Author: Equipo Kibo
# Vistas del dominio AUTH — login, logout, registro, perfil, mascotas

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from .forms import MascotaForm, ProfileUpdateForm, RegisterForm, UserUpdateForm
from .models import Mascota, UserProfile


def register_view(request):
    """Registro de usuarios cliente (is_admin=False por defecto)."""
    if request.user.is_authenticated:
        return redirect('store:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, _('Cuenta creada correctamente. ¡Bienvenido a Kibo!'))
            return redirect('store:home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Login con formulario estándar de Django."""
    if request.user.is_authenticated:
        return redirect('store:home')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, _('Bienvenido, %s.') % user.username)

        is_domain_admin = UserProfile.objects.filter(user=user, is_admin=True).exists()
        if is_domain_admin:
            return redirect('admin_panel:dashboard')
        return redirect('store:home')

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Cierra sesión y redirige al login."""
    logout(request)
    messages.info(request, _('Sesión cerrada correctamente.'))
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """Perfil editable del usuario autenticado."""
    user: User = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Perfil actualizado correctamente.'))
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(
        request,
        'accounts/profile.html',
        {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
        },
    )


# ─────────────────────────────────────────────
# MASCOTAS
# ─────────────────────────────────────────────

@login_required
def mascota_list(request):
    """Lista de mascotas registradas por el usuario."""
    mascotas = Mascota.objects.filter(user=request.user)
    return render(request, 'accounts/mascota_list.html', {'mascotas': mascotas})


@login_required
def mascota_create(request):
    """Registrar una nueva mascota para el usuario."""
    if request.method == 'POST':
        form = MascotaForm(request.POST, request.FILES)
        if form.is_valid():
            mascota = form.save(commit=False)
            mascota.user = request.user
            mascota.save()
            messages.success(request, _('"%s" ha sido registrada.') % mascota.nombre)
            return redirect('accounts:mascota_list')
    else:
        form = MascotaForm()

    return render(request, 'accounts/mascota_form.html', {'form': form, 'action': _('Agregar')})


@login_required
def mascota_edit(request, pk):
    """Editar los datos de una mascota existente."""
    mascota = get_object_or_404(Mascota, pk=pk, user=request.user)

    if request.method == 'POST':
        form = MascotaForm(request.POST, request.FILES, instance=mascota)
        if form.is_valid():
            form.save()
            messages.success(request, _('"%s" ha sido actualizada.') % mascota.nombre)
            return redirect('accounts:mascota_list')
    else:
        form = MascotaForm(instance=mascota)

    return render(request, 'accounts/mascota_form.html', {
        'form': form,
        'action': _('Editar'),
        'mascota': mascota,
    })


@login_required
def mascota_delete(request, pk):
    """Eliminar una mascota del usuario (POST confirma)."""
    mascota = get_object_or_404(Mascota, pk=pk, user=request.user)

    if request.method == 'POST':
        nombre = mascota.nombre
        mascota.delete()
        messages.info(request, _('"%s" ha sido eliminada.') % nombre)
        return redirect('accounts:mascota_list')

    return render(request, 'accounts/mascota_confirm_delete.html', {'mascota': mascota})
