import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import override

from .path_resolver import PathResolver


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
