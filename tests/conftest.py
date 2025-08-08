import os
import sys


def _ensure_project_root_on_path() -> None:
    tests_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(tests_dir, os.pardir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


_ensure_project_root_on_path()


