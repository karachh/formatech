from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Perfil no sistema", {"fields": ("perfil",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Perfil no sistema", {"fields": ("perfil",)}),)
    list_display = UserAdmin.list_display + ("perfil",)
    list_filter = UserAdmin.list_filter + ("perfil",)