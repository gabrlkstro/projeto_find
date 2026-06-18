from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Contas e Perfis'

    def ready(self):
        from django.db.models.signals import post_migrate
        from accounts.grupos import criar_grupos_padrao
        post_migrate.connect(criar_grupos_padrao, sender=self)
        
        import accounts.signals
