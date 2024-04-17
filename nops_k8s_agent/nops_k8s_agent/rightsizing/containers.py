from dependency_injector import containers
from dependency_injector import providers

from .services import get_kubernetes_client
from .services import get_rightsizing_nops_client


class Container(containers.DeclarativeContainer):
    rightsizing_client = providers.Factory(get_rightsizing_nops_client)

    kubernetes_client = providers.Singleton(get_kubernetes_client)
