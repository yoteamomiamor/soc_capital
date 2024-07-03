import os
import sys
import inspect
from pathlib import Path


def get_path():
    try:
        if '__main__' in sys.modules and hasattr(sys.modules['__main__'], '__file__'):
            return os.path.abspath(sys.modules['__main__'].__file__)
    except (AttributeError, KeyError):
        pass

    try:
        if hasattr(sys, 'argv') and sys.argv:
            return os.path.abspath(sys.argv[0])
    except (AttributeError, IndexError):
        pass

    try:
        return os.path.abspath(inspect.getfile(inspect.currentframe()))
    except (TypeError, ValueError):
        pass

    try:
        return str(Path(__file__).resolve())
    except NameError:
        pass

    return os.path.abspath(os.getcwd())


def goto(line: int, file: str | None = None) -> None:
    file = file or get_path()
    with open(os.path.abspath(file), encoding='utf-8') as file:
        code = ''.join(file.readlines()[line-1:])
        exec(code)
        sys.exit()
