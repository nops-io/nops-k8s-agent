from dependency_injector import containers, providers

from .services import get_rightsizing_client


class Container(containers.DeclarativeContainer):
    rightsizing_client = providers.Factory(
        get_rightsizing_client
    )
