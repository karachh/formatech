from django import forms

from .models import Presenca

PREFIXO = "perseverante_"


class PresencaForm(forms.Form):
    """Um campo por perseverante da grade, já marcado com a situação inicial."""

    def __init__(self, *args, grade=(), **kwargs):
        super().__init__(*args, **kwargs)
        for perseverante, situacao in grade:
            self.fields[f"{PREFIXO}{perseverante.pk}"] = forms.ChoiceField(
                label=perseverante.nome,
                choices=Presenca.Situacao.choices,
                initial=situacao,
                widget=forms.RadioSelect,
            )

    def situacoes(self):
        """{perseverante_id: situacao}, no formato que o serviço recebe."""
        return {int(nome.removeprefix(PREFIXO)): valor for nome, valor in self.cleaned_data.items()}
