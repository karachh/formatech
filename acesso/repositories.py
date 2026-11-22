from django.contrib.auth import authenticate

from .models import Usuario


def autenticar_usuario(username, senha):
    """Devolve o Usuario se as credenciais forem válidas; senão, None."""
    return authenticate(username=username, password=senha)

def listar_usuarios_formadores():
    return list(Usuario.objects.filter(perfil=Usuario.Perfil.FORMADOR).order_by("username"))
