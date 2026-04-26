from typing import Optional, Any
from settings import log_level
from logging import Logger, getLogger


class LoggingMixin:
    """
    Mixin class that creates custom logger for pipeline component.
    """
    logger_name: Optional[str]
    logger_level: Optional[int]
    _logger: Logger = None

    def __init_subclass__(
        cls,
        logger_name: Optional[str] = None,
        logger_level: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        cls.logger_name = logger_name
        cls.logger_level = logger_level
        super().__init_subclass__(**kwargs)

    @property
    def logger(self) -> Logger:
        if self._logger is None:
            self.logger_name = self.logger_name or self.__class__.__name__
            self.logger_level = self.logger_level or log_level
            self._logger = getLogger(name=self.logger_name)
            self.logger.setLevel(level=self.logger_level)
        return self._logger
