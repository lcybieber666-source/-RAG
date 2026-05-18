import os


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def resolve_relative_path(base_dir: str, path_value: str) -> str:
    normalized = path_value.replace("\\", os.sep).replace("/", os.sep)
    if os.path.isabs(normalized):
        return os.path.normpath(normalized)
    return os.path.normpath(os.path.join(base_dir, normalized))
