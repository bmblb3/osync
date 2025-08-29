import os
from pathlib import Path


def _get_envvar_or_error(varname: str):
    envvar = dict(os.environ).get(varname)
    if envvar is None:
        raise ValueError(f"Undefined or empty environment variable '{varname}'")
    return envvar


class PathResolver:
    def __init__(
        self, proxy_root: str | None = None, remote_user_host: str | None = None
    ):
        if proxy_root is None:
            proxy_root = _get_envvar_or_error("OSYNC_PROXY_ROOT")

        if remote_user_host is None:
            remote_user_host = _get_envvar_or_error("OSYNC_REMOTE_USER_HOST")

        self.proxy_root: Path = Path(proxy_root)
        self.remote_user_host: str = remote_user_host

    def _to_remote(self, path: str):
        path_obj = Path(path)
        if path_obj.resolve().is_relative_to(self.proxy_root):
            return Path("/") / path_obj.resolve().relative_to(self.proxy_root)

        if not path_obj.is_absolute():
            raise ValueError("Can't work with a path outside OSYNC_PROXY_ROOT")

        return path_obj

    def _to_local(self, path: str):
        path_obj = Path(path)
        if path_obj.resolve().is_relative_to(self.proxy_root):
            return path_obj.resolve()

        if not path_obj.is_absolute():
            return path_obj.resolve()

        return self.proxy_root / Path(path[1:])

    def to_remote(self, path: str):
        return self.remote_user_host + ":" + self._to_remote(path).as_posix()

    def to_local(self, path: str):
        return self._to_local(path).as_posix()
