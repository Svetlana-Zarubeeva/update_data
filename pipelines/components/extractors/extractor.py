from abc import ABC

from pipelines.components.mixins.logging_mixin import LoggingMixin
from pipelines.components.mixins.tracing_mixin import TracingMixin
from pipelines.interfaces import IExtractor


class Extractor(IExtractor, LoggingMixin, TracingMixin, ABC):
    """
    Base class for extractors.
    """
