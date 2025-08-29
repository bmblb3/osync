import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import override
from unittest.mock import patch

from osync import cli
from osync.filter_group import FilterGroup
from osync.findup import findup
from osync.path_resolver import PathResolver


# ---
# CLI
# ---
class TestCLI(unittest.TestCase):
    def test_push_argument(self):
        args = cli.main(["--push", "some/path"])
        self.assertTrue(args.push)
        self.assertFalse(args.pull)
        self.assertEqual(args.path, "some/path")

    def test_pull_argument(self):
        args = cli.main(["--pull", "another/path"])
        self.assertTrue(args.pull)
        self.assertFalse(args.push)
        self.assertEqual(args.path, "another/path")

    def test_force_argument(self):
        args = cli.main(["--push", "--force", "foo/bar"])
        self.assertTrue(args.force)

    def test_noforce_argument(self):
        args = cli.main(["--push", "foo/bar"])
        self.assertFalse(args.force)

    def test_dryrun_argument(self):
        args = cli.main(["--push", "--dry-run", "foo/bar"])
        self.assertTrue(args.dry_run)

    def test_nodryrun_argument(self):
        args = cli.main(["--push", "foo/bar"])
        self.assertFalse(args.dry_run)

    def test_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            _ = cli.main(["--push", "--pull", "foo"])

    def test_neither_in_group(self):
        with self.assertRaises(SystemExit):
            _ = cli.main(["foo"])


# ------------
# FILTER_GROUP
# ------------
def filtergroup(**kwargs):  # pyright:ignore[reportMissingParameterType,reportUnknownParameterType]
    defaults = {
        "direction": "push",
        "kind": "include",
        "patterns": ["pat"],
    }
    return FilterGroup(**{**defaults, **kwargs})  # pyright:ignore[reportArgumentType]


class TestFilterGroup_ArgsValidation(unittest.TestCase):
    def test_direction_enum(self):
        for value in ["push", "pull"]:
            with self.subTest(direction=value):
                _ = filtergroup(direction=value)

        with self.assertRaisesRegex(ValueError, "not a valid Direction"):
            _ = filtergroup(direction="invalid")

    def test_kind_enum(self):
        for value in ["include", "exclude"]:
            with self.subTest(kind=value):
                _ = filtergroup(kind=value)

        with self.assertRaisesRegex(ValueError, "not a valid Kind"):
            _ = filtergroup(kind="invalid")

    def test_empty_patterns(self):
        with self.assertRaisesRegex(
            ValueError, "List should have at least 1 item after validation"
        ):
            _ = filtergroup(patterns=[])
        with self.assertRaisesRegex(ValueError, "Input should be a valid list"):
            _ = filtergroup(patterns=None)


class TestFilterGroup_KindToRsyncArgs(unittest.TestCase):
    def test_include_pattern(self):
        fp = filtergroup(kind="include", patterns=["pat"])
        expected = ["--include=pat"]
        self.assertEqual(fp.rsync_args(), expected)

    def test_exclude_pattern(self):
        fp = filtergroup(kind="exclude", patterns=["pat"])
        expected = ["--exclude=pat"]
        self.assertEqual(fp.rsync_args(), expected)


class TestFilterGroup_MultiplPatternsToRsyncArgs(unittest.TestCase):
    def test_multiple_patterns(self):
        fp = filtergroup(kind="include", patterns=["pat1", "pat2"])
        expected = ["--include=pat1", "--include=pat2"]
        self.assertEqual(fp.rsync_args(), expected)


# ------
# FINDUP
# ------
class TestFindup(unittest.TestCase):
    base_dir: str = ""

    @override
    def setUp(self):
        self.base_dir = tempfile.mkdtemp()
        os.chdir(self.base_dir)

    @override
    def tearDown(self):
        shutil.rmtree(self.base_dir)

    def test_find_file_in_current_dir(self):
        filename = "testfile.txt"
        filepath = os.path.join(self.base_dir, filename)
        with open(filepath, "w") as f:
            _ = f.write("test content")
        found = findup(filename)
        self.assertEqual(found, filepath)

    def test_find_file_in_parent_dir(self):
        filename = "testfile.txt"
        filepath = os.path.join(self.base_dir, filename)
        sub_dir = os.path.join(self.base_dir, "subdir")
        os.mkdir(sub_dir)
        with open(filepath, "w") as f:
            _ = f.write("test content")
        os.chdir(sub_dir)
        found = findup(filename)
        self.assertEqual(found, filepath)

    def test_file_not_found_raises(self):
        sub_dir = os.path.join(self.base_dir, "subdir")
        os.mkdir(sub_dir)
        os.chdir(sub_dir)
        with self.assertRaises(LookupError):
            _ = findup("nonexistent.txt")


# -------------
# PATH_RESOLVER
# -------------
class TestPathResolver_EnvVarChecks(unittest.TestCase):
    def test_with_envvars(self):
        with patch.dict(
            os.environ,
            {
                "OSYNC_PROXY_ROOT": "new_proxy_root",
                "OSYNC_REMOTE_USER_HOST": "new_remote_user@new_host",
            },
        ):
            assert os.environ["OSYNC_PROXY_ROOT"] == "new_proxy_root"
            assert os.environ["OSYNC_REMOTE_USER_HOST"] == "new_remote_user@new_host"
            path_resolver = PathResolver()
            self.assertEqual("new_proxy_root", path_resolver.proxy_root.as_posix())
            self.assertEqual("new_remote_user@new_host", path_resolver.remote_user_host)

    def test_without_remoteuserhost_envvar(self):
        with patch.dict(os.environ, {"OSYNC_PROXY_ROOT": ""}):
            with self.assertRaisesRegex(
                ValueError, r"(E|e)nvironment (V|v)ariable.*OSYNC_REMOTE_USER_HOST"
            ):
                _ = PathResolver()

    def test_without_proxyroot_envvar(self):
        with patch.dict(os.environ, {"OSYNC_REMOTE_USER_HOST": ""}):
            with self.assertRaisesRegex(
                ValueError, "(E|e)nvironment (V|v)ariable.*OSYNC_PROXY_ROOT"
            ):
                _ = PathResolver()


class TestPathResolver(unittest.TestCase):
    proxy_root: str = ""
    cwd: str = ""
    path_resolver: PathResolver = PathResolver(".", ".")

    @override
    def setUp(self) -> None:
        self.proxy_root = tempfile.mkdtemp()
        self.path_resolver = PathResolver(self.proxy_root, "user@host")
        self.cwd = tempfile.mkdtemp()
        os.chdir(self.cwd)

    @override
    def tearDown(self) -> None:
        shutil.rmtree(self.proxy_root, ignore_errors=True)
        shutil.rmtree(self.cwd, ignore_errors=True)

    # TO_REMOTE
    def test__with_abspath_just_under_proxy_root__gets_remote(self) -> None:
        file = Path(self.proxy_root) / "somefile.txt"

        result = self.path_resolver.to_remote(str(file))
        expected = "user@host:/somefile.txt"
        self.assertEqual(result, expected)

    def test__with_relpath_just_under_proxy_root__gets_remote(self) -> None:
        os.chdir(self.proxy_root)
        file = Path("./somefile.txt")

        result = self.path_resolver.to_remote(str(file))
        expected = "user@host:/somefile.txt"
        self.assertEqual(result, expected)

    def test__with_abspath_outside_proxy_root__gets_remote(self) -> None:
        remote_abs_path = "/tmp/remote/abs/path/file.txt"

        result = self.path_resolver.to_remote(remote_abs_path)
        expected = "user@host:/tmp/remote/abs/path/file.txt"
        self.assertEqual(result, expected)

    def test__with_relpath_outside_proxy_root__raises_error_on_getting_remote(
        self,
    ) -> None:
        file = Path("./somefile.txt")

        with self.assertRaisesRegex(ValueError, "Can't work with a path outside"):
            _ = self.path_resolver.to_remote(str(file))

    def test__with_changed_hostname(self) -> None:
        file = Path(self.proxy_root) / "somefile.txt"

        self.path_resolver.remote_user_host = "newuser@newhost"
        result = self.path_resolver.to_remote(str(file))
        expected = "newuser@newhost:/somefile.txt"
        self.assertEqual(result, expected)

    # TO_LOCAL
    def test__with_abspath_just_under_proxy_root__gets_local(self) -> None:
        file = Path(self.proxy_root) / "somefile.txt"

        result = self.path_resolver.to_local(str(file))
        expected = self.proxy_root + "/somefile.txt"
        self.assertEqual(result, expected)

    def test__with_relpath_just_under_proxy_root__gets_local(self) -> None:
        os.chdir(self.proxy_root)
        file = Path("./somefile.txt")

        result = self.path_resolver.to_local(str(file))
        expected = self.proxy_root + "/somefile.txt"
        self.assertEqual(result, expected)

    def test__with_abspath_outside_proxy_root__gets_local(self) -> None:
        remote_abs_path = "/tmp/remote/abs/path/file.txt"

        result = self.path_resolver.to_local(remote_abs_path)
        expected = self.proxy_root + "/tmp/remote/abs/path/file.txt"
        self.assertEqual(result, expected)

    def test__with_relpath_outside_proxy_root__gets_local(
        self,
    ) -> None:
        file = Path("./somefile.txt")

        result = self.path_resolver.to_local(str(file))
        expected = self.cwd + "/somefile.txt"
        self.assertEqual(result, expected)


# -------------
# RSYNC_COMMAND
# -------------
# class DummyPattern(FilePattern):
#     def __init__(
#         self,
#         push: bool = False,
#         pull: bool = False,
#         rsync_args: list[str] | None = None,
#     ):
#         super().__init__(desc="", type="include", patterns=[""], push=False, pull=False)
#         self.push: bool = push
#         self.pull: bool = pull
#         self._rsync_args: list[str] = rsync_args or []
#
#     @override
#     def rsync_args(self):
#         return self._rsync_args
#
#
# class TestRsyncCommand(unittest.TestCase):
#     def test_env_var(self):
#         with patch.dict(os.environ, {"OSYNC_REMOTE_USER_HOST": "NEWUSER@NEWHOST"}):
#             assert os.environ["OSYNC_REMOTE_USER_HOST"] == "NEWUSER@NEWHOST"
#             cmd = RsyncCommand(
#                 push=True,
#                 pull=False,
#                 force=False,
#                 file_patterns=[],
#                 source="/src/",
#                 dest="/dst/",
#             )
#             self.assertEqual(cmd.args[-1:], ["NEWUSER@NEWHOST:/dst/"])
#
#     def test_raises_error_when_no_env_var(self):
#         with self.assertRaisesRegex(ValueError, "(E|e)nvironment (V|v)ariable"):
#             _ = RsyncCommand(
#                 push=True,
#                 pull=False,
#                 force=False,
#                 file_patterns=[],
#                 source="/src/",
#                 dest="/dst/",
#             )
#
#     def test_build_has_base_args(self):
#         cmd = RsyncCommand(
#             remote_user_host="user@host",
#             push=True,
#             pull=False,
#             force=False,
#             file_patterns=[],
#             source="/src/",
#             dest="/dst/",
#         )
#         self.assertIn("rsync", cmd.args)
#         self.assertIn("--recursive", cmd.args)
#
#     def test_build_push(self):
#         cmd = RsyncCommand(
#             remote_user_host="user@host",
#             push=True,
#             pull=False,
#             force=False,
#             file_patterns=[
#                 DummyPattern(push=True, rsync_args=["pusharg"]),
#                 DummyPattern(pull=True, rsync_args=["pullarg"]),
#                 DummyPattern(push=True, pull=True, rsync_args=["botharg"]),
#             ],
#             source="/src/",
#             dest="/dst/",
#         )
#         self.assertIn("rsync", cmd.args)
#         self.assertIn("pusharg", cmd.args)
#         self.assertNotIn("pullarg", cmd.args)
#         self.assertIn("botharg", cmd.args)
#         self.assertEqual(cmd.args[-2:], ["/src/", "user@host:/dst/"])
#
#     def test_build_pull(self):
#         cmd = RsyncCommand(
#             remote_user_host="user@host",
#             push=False,
#             pull=True,
#             force=False,
#             file_patterns=[
#                 DummyPattern(push=True, rsync_args=["pusharg"]),
#                 DummyPattern(pull=True, rsync_args=["pullarg"]),
#                 DummyPattern(push=True, pull=True, rsync_args=["botharg"]),
#             ],
#             source="/src/",
#             dest="/dst/",
#         )
#         self.assertIn("rsync", cmd.args)
#         self.assertNotIn("pusharg", cmd.args)
#         self.assertIn("pullarg", cmd.args)
#         self.assertIn("botharg", cmd.args)
#         self.assertEqual(cmd.args[-2:], ["user@host:/src/", "/dst/"])
#
#     def test_build_force(self):
#         cmd = RsyncCommand(
#             remote_user_host="user@host",
#             push=True,
#             pull=False,
#             force=True,
#             file_patterns=[],
#             source="/src/",
#             dest="/dst/",
#         )
#         self.assertNotIn("--exclude=*", cmd.args)
#
#     def test_build_noforce(self):
#         cmd = RsyncCommand(
#             remote_user_host="user@host",
#             push=True,
#             pull=False,
#             force=False,
#             file_patterns=[],
#             source="/src/",
#             dest="/dst/",
#         )
#         self.assertIn("--exclude=*", cmd.args)
#
#     def test_build_multiple_pushargs(self):
#         cmd = RsyncCommand(
#             remote_user_host="user@host",
#             push=True,
#             pull=False,
#             force=False,
#             file_patterns=[
#                 DummyPattern(push=True, rsync_args=["pushargA1", "pushargA2"]),
#                 DummyPattern(push=True, rsync_args=["pushargB1"]),
#                 DummyPattern(pull=True, rsync_args=["pullarg"]),
#                 DummyPattern(push=True, pull=True, rsync_args=["botharg"]),
#             ],
#             source="/src/",
#             dest="/dst/",
#         )
#         self.assertIn("rsync", cmd.args)
#         self.assertIn("pushargA1", cmd.args)
#         self.assertIn("pushargA2", cmd.args)
#         self.assertIn("pushargB1", cmd.args)
#         self.assertNotIn("pullarg", cmd.args)
#         self.assertIn("botharg", cmd.args)
#         self.assertEqual(cmd.args[-2:], ["/src/", "user@host:/dst/"])
#
#     def test_build_with_dryrun(self):
#         cmd = RsyncCommand(
#             remote_user_host="user@host",
#             push=True,
#             pull=False,
#             force=False,
#             file_patterns=[],
#             source="/src/",
#             dest="/dst/",
#             dry_run=True,
#         )
#         self.assertIn("rsync", cmd.args)
#         self.assertIn("--recursive", cmd.args)
#         self.assertIn("--dry-run", cmd.args)
#
#     def test_build_without_dryrun(self):
#         cmd = RsyncCommand(
#             remote_user_host="user@host",
#             push=True,
#             pull=False,
#             force=False,
#             file_patterns=[],
#             source="/src/",
#             dest="/dst/",
#         )
#         self.assertIn("rsync", cmd.args)
#         self.assertIn("--recursive", cmd.args)
#         self.assertNotIn("--dry-run", cmd.args)
