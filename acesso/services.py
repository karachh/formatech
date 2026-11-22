from django.core.exceptions import ValidationError

from . import repositories


def autenticar(username, senha):
    usuario = repositories.autenticar_usuario(username, senha)
    if usuario is None:
        raise ValidationError("Usuário ou senha inválidos.")
    return usuario

def listar_usuarios_formadores():
    """Logins que podem ser vinculados a um formador (US018)."""
    return repositories.listar_usuarios_formadores()
