import unicodedata
from typing import Dict, Any, List, Optional


def json_path_get(data: Dict[str, Any], path: str | List[str], default: Optional[Any] = None) -> Any:
    """
    Returns value from data by JSON path. If more than one path has been passed, first founded value will be returned.
    """
    if isinstance(path, str):
        path = [path]

    for _path in path:
        result = data
        parts = _path.split(".")

        for i, part in enumerate(parts):
            if part == "$":
                continue
            if isinstance(result, dict):
                result = result.get(part)
            elif isinstance(result, list):
                element_result = None
                for element in result:
                    if isinstance(element, dict):
                        element_result = element.get(part)
                    if element_result is not None:
                        break
                result = element_result
            else:
                break
        else:
            return result

    return default


def normalize_str(string: str) -> str:
    """
    Normalizes string in next steps:
     - NFKD-form normalization,
     - ASCII encoding-decoding,
     - lower-case conversation,
     - white-space stripping.
    """
    return unicodedata.normalize('NFKD', string).encode('ascii', 'ignore').decode('ascii').lower().strip()
