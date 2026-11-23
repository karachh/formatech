from django import forms


class CicloRelatorioForm(forms.Form):
    ciclo = forms.ChoiceField(label="Ciclo encerrado", required=False)

    def __init__(self, *args, ciclos=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ciclo"].choices = [("", "Selecione um ciclo")] + [
            (str(ciclo.pk), ciclo.nome) for ciclo in ciclos
        ]
