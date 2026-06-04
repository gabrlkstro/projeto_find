from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend que permite ao usuário se autenticar
    utilizando tanto o seu 'username' quanto o seu 'email'.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        try:
            # Busca pelo e-mail ou pelo nome de usuário (case-insensitive)
            user = UserModel.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except UserModel.DoesNotExist:
            return None
        except UserModel.MultipleObjectsReturned:
            # Caso existam múltiplos usuários com o mesmo e-mail, seleciona o primeiro
            user = UserModel.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
