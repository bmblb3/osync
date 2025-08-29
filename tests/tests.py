import os
import shutil
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import final, override
from unittest.mock import patch

from osync import cli
from osync.filter_group import Direction, FilterGroup
from osync.findup import findup
from osync.path_resolver import PathResolver
from osync.rsync import RsyncCommand


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
        self.assertEqual(fp.rsync_args, expected)

    def test_exclude_pattern(self):
        fp = filtergroup(kind="exclude", patterns=["pat"])
        expected = ["--exclude=pat"]
        self.assertEqual(fp.rsync_args, expected)


class TestFilterGroup_MultiplPatternsToRsyncArgs(unittest.TestCase):
    def test_multiple_patterns(self):
        fp = filtergroup(kind="include", patterns=["pat1", "pat2"])
        expected = ["--include=pat1", "--include=pat2"]
        self.assertEqual(fp.rsync_args, expected)


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
def rsynccommand():
    return RsyncCommand(
        direction=Direction.PUSH,
        source="/src/",
        dest="user@host:/dst/",
        filter_groups=[],
    )


@dataclass
class DummmyFilterGroup:
    direction: Direction
    rsync_args: list[str]


class TestRsyncCommand(unittest.TestCase):
    def test_force(self):
        rsync_cmd_noforce = rsynccommand()
        rsync_cmd_noforce.force = False
        rsync_cmd_force = rsynccommand()
        rsync_cmd_force.force = True

        rsync_cmd_noforce.build()
        rsync_cmd_force.build()

        self.assertIn("--exclude=*", rsync_cmd_noforce.args)
        self.assertNotIn("--exclude=*", rsync_cmd_force.args)

    def test_dryrun(self):
        rsync_cmd_nodryrun = rsynccommand()
        rsync_cmd_nodryrun.dry_run = False
        rsync_cmd_dryrun = rsynccommand()
        rsync_cmd_dryrun.dry_run = True

        rsync_cmd_nodryrun.build()
        rsync_cmd_dryrun.build()

        self.assertNotIn("--dry-run", rsync_cmd_nodryrun.args)
        self.assertIn("--dry-run", rsync_cmd_dryrun.args)

    def test_push(self):
        rsync_cmd = rsynccommand()
        rsync_cmd.direction = Direction.PUSH
        rsync_cmd.filter_groups = [  # pyright:ignore[reportAttributeAccessIssue]
            DummmyFilterGroup(direction=Direction.PUSH, rsync_args=["pusharg"]),
            DummmyFilterGroup(direction=Direction.PULL, rsync_args=["pullarg"]),
        ]
        rsync_cmd.build()

        self.assertIn("pusharg", rsync_cmd.args)
        self.assertNotIn("pullarg", rsync_cmd.args)

    def test_pull(self):
        rsync_cmd = rsynccommand()
        rsync_cmd.direction = Direction.PULL
        rsync_cmd.filter_groups = [  # pyright:ignore[reportAttributeAccessIssue]
            DummmyFilterGroup(direction=Direction.PUSH, rsync_args=["pusharg"]),
            DummmyFilterGroup(direction=Direction.PULL, rsync_args=["pullarg"]),
        ]
        rsync_cmd.build()

        self.assertNotIn("pusharg", rsync_cmd.args)
        self.assertIn("pullarg", rsync_cmd.args)

    def test_multiple_groups(self):
        rsync_cmd = rsynccommand()
        rsync_cmd.direction = Direction.PULL
        rsync_cmd.filter_groups = [  # pyright:ignore[reportAttributeAccessIssue]
            DummmyFilterGroup(direction=Direction.PUSH, rsync_args=["pushargA"]),
            DummmyFilterGroup(
                direction=Direction.PUSH, rsync_args=["pushargB1", "pushargB2"]
            ),
            DummmyFilterGroup(direction=Direction.PULL, rsync_args=["pullarg"]),
        ]
        rsync_cmd.build()

        self.assertNotIn("pushargA", rsync_cmd.args)
        self.assertNotIn("pushargB1", rsync_cmd.args)
        self.assertNotIn("pushargB2", rsync_cmd.args)
        self.assertIn("pullarg", rsync_cmd.args)
