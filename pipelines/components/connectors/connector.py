from abc import ABC
from types import TracebackType
from typing import Self, Type, ContextManager, Optional, AsyncContextManager

from pipelines.components.mixins.logging_mixin import LoggingMixin
from pipelines.components.mixins.tracing_mixin import TracingMixin
from pipelines.interfaces import IConnector


class Connector(IConnector, ContextManager, LoggingMixin, TracingMixin, ABC):
    """
    Base class for connectors.
    """

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, exc_type: Type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> Optional[bool]:
        self.close()


class AsyncConnector(IConnector, AsyncContextManager, LoggingMixin, TracingMixin, ABC):
    """
    Base class for async connectors.
    """

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> Optional[bool]:
        await self.close()
