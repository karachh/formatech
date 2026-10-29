from functools import wraps

from django.core.exceptions import PermissionDenied

from .models import Usuario


def coordenador_required(view):
    

    @wraps(view)
    def envolvida(request, *args, **kwargs):
        if getattr(request.user, "perfil", None) != Usuario.Perfil.COORDENADOR:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return envolvida