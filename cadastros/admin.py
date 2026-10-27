from django.contrib import admin

from .models import Ciclo


class CicloAdmin(admin.ModelAdmin):
    list_display = ["nome", "inicio", "fim", "situacao"]


admin.site.register(Ciclo, CicloAdmin)
