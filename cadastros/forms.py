from django import forms

from .models import Tema
# type="date" mostra o calendário do navegador, que envia a data no formato AAAA-MM-DD.
CAMPO_DATA = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class CicloForm(forms.Form):
    """Só converte o que veio da tela. Quem valida a regra é o services."""

    nome = forms.CharField(max_length=100)
    inicio = forms.DateField(label="Início", widget=CAMPO_DATA)
    fim = forms.DateField(widget=CAMPO_DATA)

    def __init__(self, *args, datas_editaveis=True, **kwargs):
        super().__init__(*args, **kwargs)
        # disabled ignora o valor enviado e usa o initial: as datas voltam como estavam.
        self.fields["inicio"].disabled = self.fields["fim"].disabled = not datas_editaveis


class TemaForm(forms.Form):
    """Só converte o que veio da tela. Quem valida a regra é o services."""

    nome = forms.CharField(max_length=150)
    tipo = forms.ChoiceField(choices=Tema.Tipo.choices)
    rotulo = forms.CharField(label="Rótulo na apostila", max_length=50, required=False)


class FormadorForm(forms.Form):
    nome = forms.CharField(max_length=150)
    inicio_servico = forms.DateField(label="Início de serviço", widget=CAMPO_DATA)
    capacitado = forms.BooleanField(label="Capacitado", required=False)


class CicloFiltroForm(forms.Form):
    ciclo = forms.ChoiceField(label="Ciclo", required=False)

    def __init__(self, *args, ciclos=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ciclo"].choices = [("", "Selecione um ciclo")] + [
            (str(ciclo.pk), ciclo.nome) for ciclo in ciclos
        ]


class PerseveranteForm(forms.Form):
    nome = forms.CharField(max_length=150)
    ciclo_id = forms.ChoiceField(label="Ciclo")

    def __init__(self, *args, ciclos=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ciclo_id"].choices = [("", "Selecione um ciclo")] + [
            (str(ciclo.pk), ciclo.nome) for ciclo in ciclos
        ]