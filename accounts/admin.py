from django.contrib import admin

from .models import Mascota, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'is_admin')
    list_filter = ('is_admin',)
    search_fields = ('user__username', 'user__email')


@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'raza', 'edad', 'peso', 'user')
    list_filter = ('tipo',)
    search_fields = ('nombre', 'user__username')
