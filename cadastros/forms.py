from django import forms

# type="date" mostra o calendário do navegador, que envia a data no formato AAAA-MM-DD.
CAMPO_DATA = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class CicloForm(forms.Form):
    """Só converte o que veio da tela. Quem valida a regra é o services.abrir_ciclo."""

    nome = forms.CharField(max_length=100)
    inicio = forms.DateField(label="Início", widget=CAMPO_DATA)
    fim = forms.DateField(widget=CAMPO_DATA)
