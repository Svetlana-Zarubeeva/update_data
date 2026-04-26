from abc import ABC

from pipelines.components.mixins.logging_mixin import LoggingMixin
from pipelines.components.mixins.tracing_mixin import TracingMixin
from pipelines.interfaces import ILoader


class Loader(ILoader, LoggingMixin, TracingMixin, ABC):
    """
    Base class for loaders.
    """
