from django.contrib import admin

from .models import Formacao


class FormacaoAdmin(admin.ModelAdmin):
    list_display = ["data", "tema", "formador", "situacao"]


admin.site.register(Formacao, FormacaoAdmin)