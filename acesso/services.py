from django.core.exceptions import ValidationError

from . import repositories


def autenticar(username, senha):
    usuario = repositories.autenticar_usuario(username, senha)
    if usuario is None:
        raise ValidationError("Usuário ou senha inválidos.")
    return usuario