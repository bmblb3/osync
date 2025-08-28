import os
from pathlib import Path


class PathResolver:
    def __init__(self, proxy_root: str | None = None):
        if proxy_root is None:
            proxy_root = dict(os.environ).get("OSYNC_PROXY_ROOT", "")
        if proxy_root == "":
            raise ValueError("Undefined or empty environment variable OSYNC_PROXY_ROOT")
        self.proxy_root: Path = Path(proxy_root)

    def to_remote(self, path: str) -> Path:
        path_obj = Path(path)
        if path_obj.resolve().is_relative_to(self.proxy_root):
            return Path("/") / path_obj.resolve().relative_to(self.proxy_root)
        if not path_obj.is_absolute():
            raise ValueError(
                "Cannot determine remote path for a relative path outside the OSYNC_PROXY_ROOT"
            )
        return path_obj

    def to_local(self, path: str) -> Path:
        path_obj = Path(path)
        if path_obj.resolve().is_relative_to(self.proxy_root):
            return path_obj.resolve()
        if not path_obj.is_absolute():
            return path_obj.resolve()
        return self.proxy_root / Path(path[1:])
