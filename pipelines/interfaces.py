from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Literal, Any, TypeAlias, Awaitable

ModeLiteral: TypeAlias = Literal["daily", "backfill"]
ExtractType = TypeVar("ExtractType")
LoadType = TypeVar("LoadType")


class IConnector(ABC):

    @abstractmethod
    def connect(self) -> None | Awaitable[None]:
        raise NotImplementedError()

    @abstractmethod
    def close(self) -> None | Awaitable[None]:
        raise NotImplementedError()


class IExtractor(ABC, Generic[ExtractType]):
    mode: ModeLiteral

    @abstractmethod
    def __init__(self, *connectors: IConnector, mode: ModeLiteral, **kwargs: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def extract(self, *args: Any) -> ExtractType:
        """Извлекает данные и возвращает их в виде списка словарей."""
        raise NotImplementedError()


class ITransformer(ABC, Generic[ExtractType, LoadType]):

    @abstractmethod
    def transform(self, data: ExtractType) -> LoadType:
        """Применяет трансформации к данным."""
        raise NotImplementedError()


class ILoader(ABC, Generic[LoadType]):
    mode: ModeLiteral

    @abstractmethod
    def __init__(self, *connectors: IConnector, mode: ModeLiteral, **kwargs: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def load(self, data: LoadType) -> Any:
        """Загружает данные в целевую систему."""
        raise NotImplementedError()


class IMetrics(ABC, Generic[ExtractType]):
    """Интерфейс для сбора data-aware метрик."""

    @abstractmethod
    def log_pre_run_metrics(self, data: ExtractType) -> None:
        """Логирует метрики перед загрузкой, используя извлеченные данные."""
        raise NotImplementedError()

    @abstractmethod
    def log_post_run_metrics(self, data: LoadType) -> None:
        """Логирует метрики после загрузки, проверяя состояние целевой таблицы."""
        raise NotImplementedError()
