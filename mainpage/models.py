"""
Models do mainpage — re-exporta dos apps modulares para compatibilidade.
Os models reais agora vivem em accounts/, items/ e chats/.
"""
from accounts.models import Profile  # noqa: F401
from items.models import ArquivoMidia, Categoria, Item  # noqa: F401
from chats.models import Chat, Mensagem  # noqa: F401
