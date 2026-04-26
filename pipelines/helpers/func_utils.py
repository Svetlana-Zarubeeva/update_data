import inspect
import logging
import sys
from functools import wraps
from types import ModuleType
from typing import Callable, Any, Type, AsyncIterable, List, TypeVar, Tuple, Iterable, Optional, Iterator, AsyncIterator

_T = TypeVar("_T")
_GeneratorFunc = Callable[..., Iterator[_T] | AsyncIterator[_T]]

_DEFAULT_RETRIES = 5
_DEFAULT_BATCH_SIZE = 1000


def retry_if(*catch: BaseException | Type[BaseException], retries: int = _DEFAULT_RETRIES) -> Callable[[Callable], Callable]:
    """
    Applies retries functional to target callable.
    """
    def wrapper(func: Callable) -> Callable:

        @wraps(func)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            last_ex = None
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except catch as ex:
                    last_ex = ex
            if last_ex:
                raise last_ex

        return _wrapper

    return wrapper


async def release_async_gen(agen: AsyncIterable[_T]) -> List[_T]:
    """
    Iterates asynchronously through async generator and returns results as list.
    """
    result = []
    async for item in agen:
        result.append(item)
    return result


def as_batches(data: Iterable[_T], *, batch_size: int = _DEFAULT_BATCH_SIZE) -> Iterable[List[_T]]:
    """
    Iterates items as batches.
    """
    batch = []
    for item in data:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if len(batch) > 0:
        yield batch


def progress(
    message: str,
    every: int = 1,
    level: int = logging.INFO,
    logger: Optional[logging.Logger] = None,
    skip_zero: bool = True,
    skip_last: bool = False,
    progress_func: Optional[Callable[[_T], int]] = None,
    **kwargs: Any,
) -> Callable[[_GeneratorFunc], _GeneratorFunc]:
    """
    Applies progress logging for generator function.
    """
    log = logging.log if logger is None else logger.log
    if progress_func is None:
        progress_func = lambda x: 1

    def _wrapped(func: _GeneratorFunc) -> _GeneratorFunc:
        if inspect.isasyncgenfunction(func):
            @wraps(func)
            async def __wrapped(*args: Any, **_kwargs: Any) -> AsyncIterator[_T]:
                for key in list(kwargs.keys()):
                    if callable(kwargs[key]):
                        kwargs[key] = kwargs[key](*args, **_kwargs)
                i = 0
                async for _ in func(*args, **_kwargs):
                    i += progress_func(_)
                    yield _
                    if i % every == 0 and not (i == 0 and skip_zero):
                        log(level, message % {"i": i, **kwargs})
                if (i % every != 0) and (not skip_last):
                    log(level, message % {"i": i, **kwargs})
        else:
            @wraps(func)
            def __wrapped(*args: Any, **_kwargs: Any) -> Iterator[_T]:
                for key in list(kwargs.keys()):
                    if callable(kwargs[key]):
                        kwargs[key] = kwargs[key](*args, **_kwargs)
                i = 0
                for _ in func(*args, **_kwargs):
                    i += progress_func(_)
                    yield _
                    if i % every == 0 and not (i == 0 and skip_zero):
                        log(level, message % {"i": i, **kwargs})
                if (i % every != 0) and (not skip_last):
                    log(level, message % {"i": i, **kwargs})

        return __wrapped

    return _wrapped


def is_object_from_module(obj: object, module: ModuleType | Tuple[ModuleType] | Any) -> bool:
    """
    Check if object is derived from given module/modules.
    """
    if inspect.isclass(obj):
        obj_class = obj
    else:
        obj_class = obj.__class__

    obj_module = sys.modules.get(obj_class.__module__)
    if not isinstance(module, tuple):
        module = (module,)

    return obj_module in module


def safe_call(obj: Optional[Any], func: Callable[[Any], _T] | Type[_T]) -> Optional[_T]:
    """
    If passed object is not None, applies function and returns result, otherwise return None.
    """
    if obj is None:
        return None
    return func(obj)
