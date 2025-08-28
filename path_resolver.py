import os
from pathlib import Path


class PathResolver:
    def __init__(self, proxy_root: str | None = None):
        if proxy_root is None:
            proxy_root = os.environ["OSYNC_PROXY_ROOT"]
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


import shutil  # noqa:E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
from typing import override  # noqa:E402


class TestPathResolver(unittest.TestCase):
    proxy_root: str = ""
    cwd: str = ""
    path_resolver: PathResolver = PathResolver(".")

    @override
    def setUp(self) -> None:
        self.proxy_root = tempfile.mkdtemp()
        self.path_resolver = PathResolver(self.proxy_root)
        self.cwd = tempfile.mkdtemp()
        os.chdir(self.cwd)

    @override
    def tearDown(self) -> None:
        shutil.rmtree(self.proxy_root, ignore_errors=True)
        shutil.rmtree(self.cwd, ignore_errors=True)

    # TO_REMOTE
    def test__with_abspath_just_under_proxy_root__gets_remote(self) -> None:
        file = Path(self.proxy_root) / "somefile.txt"
        file.touch()

        result = self.path_resolver.to_remote(str(file)).as_posix()
        expected = "/somefile.txt"
        self.assertEqual(result, expected)

    def test__with_relpath_just_under_proxy_root__gets_remote(self) -> None:
        os.chdir(self.proxy_root)
        file = Path(".") / "somefile.txt"
        file.touch()

        result = self.path_resolver.to_remote(file.as_posix()).as_posix()
        expected = "/somefile.txt"
        self.assertEqual(result, expected)

    def test__with_abspath_outside_proxy_root__gets_remote(self) -> None:
        remote_abs_path = "/tmp/remote/abs/path/file.txt"

        result = self.path_resolver.to_remote(remote_abs_path).as_posix()
        expected = "/tmp/remote/abs/path/file.txt"
        self.assertEqual(result, expected)

    def test__with_relpath_outside_proxy_root__raises_error_on_getting_remote(
        self,
    ) -> None:
        file = Path(".") / "somefile.txt"
        file.touch()

        with self.assertRaisesRegex(
            ValueError, "Cannot determine remote path for a relative path outside"
        ):
            _ = self.path_resolver.to_remote(str(file))

    # TO_LOCAL
    def test__with_abspath_just_under_proxy_root__gets_local(self) -> None:
        file = Path(self.proxy_root) / "somefile.txt"
        file.touch()

        result = self.path_resolver.to_local(str(file)).as_posix()
        expected = self.proxy_root + "/somefile.txt"
        self.assertEqual(result, expected)

    def test__with_relpath_just_under_proxy_root__gets_local(self) -> None:
        os.chdir(self.proxy_root)
        file = Path(".") / "somefile.txt"
        file.touch()

        result = self.path_resolver.to_local(file.as_posix()).as_posix()
        expected = self.proxy_root + "/somefile.txt"
        self.assertEqual(result, expected)

    def test__with_abspath_outside_proxy_root__gets_local(self) -> None:
        remote_abs_path = "/tmp/remote/abs/path/file.txt"

        result = self.path_resolver.to_local(remote_abs_path).as_posix()
        expected = self.proxy_root + "/tmp/remote/abs/path/file.txt"
        self.assertEqual(result, expected)

    def test__with_relpath_outside_proxy_root__gets_local(
        self,
    ) -> None:
        file = Path(".") / "somefile.txt"
        file.touch()

        result = self.path_resolver.to_local(str(file)).as_posix()
        expected = self.cwd + "/somefile.txt"
        self.assertEqual(result, expected)


if __name__ == "__main__":
    _ = unittest.main()
