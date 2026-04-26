from abc import ABC

from pipelines.components.mixins.logging_mixin import LoggingMixin
from pipelines.interfaces import IMetrics


class Metrics(IMetrics, LoggingMixin, ABC):
    """
    Base class for metrics.
    """
