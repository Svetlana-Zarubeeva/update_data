import time
import logging
from functools import wraps
from typing import List, Callable, Any, Sized

_DEFAULT_TRACING_METHODS = (
    'extract',
    'transform',
    'load',
)


class TracingMixin:
    """
    Mixin class that provides tracing functionality for pipeline component.
    """
    def __init_subclass__(
        cls,
        tracing: bool = True,
        trace_method: str | List[str] = _DEFAULT_TRACING_METHODS,
        tracing_level: int = logging.INFO,
        **kwargs: Any,
    ):
        if tracing:
            if isinstance(trace_method, str):
                trace_method = [trace_method]
            for method in trace_method:
                if hasattr(cls, method):
                    orig_method = getattr(cls, method)
                    setattr(cls, method, cls._with_tracing(orig_method, tracing_level))
        super().__init_subclass__(**kwargs)

    @staticmethod
    def _with_tracing(method: Callable[..., Any], level: int) -> Callable[..., Any]:

        @wraps(method)
        def _wrapped(self, *args, **kwargs):
            logging.log(level, "Starting `%s`...", self.__class__.__name__)

            start_time = time.time()
            result = method(self, *args, **kwargs)
            duration = time.time() - start_time

            logging.log(level, "Finished `%s`.", self.__class__.__name__)
            logging.log(level, "Execution time: %s seconds.", round(duration, 3))
            logging.log(level, "Records processed: %s.", TracingMixin._result_shape(result))

            return result

        return _wrapped

    @staticmethod
    def _result_shape(result: Any) -> str:
        if isinstance(result, tuple):
            shape = []
            for result_ in result:
                if isinstance(result_, Sized):
                    shape.append(len(result_))
                else:
                    shape.append("N/A")
            return str(tuple(shape))
        elif isinstance(result, Sized):
            return str(len(result))
        else:
            return "N/A"
