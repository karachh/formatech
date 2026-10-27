from django import forms

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
