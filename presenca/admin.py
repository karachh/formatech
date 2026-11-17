from django.contrib import admin

from .models import Presenca


class PresencaAdmin(admin.ModelAdmin):
    list_display = ["formacao", "perseverante", "situacao"]


admin.site.register(Presenca, PresencaAdmin)
