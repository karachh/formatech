from django import forms

from cadastros.forms import CAMPO_DATA
from cadastros.models import Tema


def _opcoes_de_tema(temas):
    """CA002: temas da apostila e opcionais separados, com a opção de deixar em branco."""
    apostila = [
        (str(tema.pk), f"{tema.nome} (Apostila {tema.rotulo})" if tema.rotulo else tema.nome)
        for tema in temas
        if tema.tipo == Tema.Tipo.APOSTILA
    ]
    opcionais = [(str(tema.pk), tema.nome) for tema in temas if tema.tipo == Tema.Tipo.OPCIONAL]
    opcoes = [("", "Sem tema")]
    if apostila:
        opcoes.append(("Temas da apostila", apostila))
    if opcionais:
        opcoes.append(("Temas opcionais", opcionais))
    return opcoes


class FormacaoForm(forms.Form):
    """Só converte o que veio da tela. Quem valida a regra é o services.

    Não há campo de ciclo: o sistema o deriva da data (RN002, CA002).
    """

    data = forms.DateField(widget=CAMPO_DATA)
    tema_id = forms.ChoiceField(label="Tema", required=False)
    descricao = forms.CharField(label="Descrição", max_length=200, required=False)

    def __init__(self, *args, temas=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tema_id"].choices = _opcoes_de_tema(temas)


class AgendamentoForm(FormacaoForm):
    """Inclusão: acrescenta o formador. Na edição ele não aparece (troca é na US007)."""

    formador_id = forms.ChoiceField(label="Formador", required=False)

    field_order = ["data", "tema_id", "formador_id", "descricao"]

    def __init__(self, *args, formadores=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["formador_id"].choices = [("", "A escalar")] + [
            (str(formador.pk), formador.nome) for formador in formadores
        ]
