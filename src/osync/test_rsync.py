import os
import unittest
from typing import override
from unittest.mock import patch

from .file_pattern import FilePattern
from .rsync import RsyncCommand


class DummyPattern(FilePattern):
    def __init__(
        self,
        push: bool = False,
        pull: bool = False,
        rsync_args: list[str] | None = None,
    ):
        super().__init__(desc="", patterns=[""], push=False, pull=False)
        self.push: bool = push
        self.pull: bool = pull
        self._rsync_args: list[str] = rsync_args or []

    @override
    def rsync_args(self):
        return self._rsync_args


class TestRsyncCommand(unittest.TestCase):
    def test_env_var(self):
        with patch.dict(os.environ, {"OSYNC_REMOTE_USER_HOST": "NEWUSER@NEWHOST"}):
            assert os.environ["OSYNC_REMOTE_USER_HOST"] == "NEWUSER@NEWHOST"
            cmd = RsyncCommand(
                push=True,
                pull=False,
                force=False,
                file_patterns=[],
                source="/src/",
                dest="/dst/",
            )
            self.assertEqual(cmd.args[-1:], ["NEWUSER@NEWHOST:/dst/"])

    def test_raises_error_when_no_env_var(self):
        with self.assertRaisesRegex(ValueError, "(E|e)nvironment (V|v)ariable"):
            _ = RsyncCommand(
                push=True,
                pull=False,
                force=False,
                file_patterns=[],
                source="/src/",
                dest="/dst/",
            )

    def test_build_has_base_args(self):
        cmd = RsyncCommand(
            remote_user_host="user@host",
            push=True,
            pull=False,
            force=False,
            file_patterns=[],
            source="/src/",
            dest="/dst/",
        )
        self.assertIn("rsync", cmd.args)
        self.assertIn("--recursive", cmd.args)

    def test_build_push(self):
        cmd = RsyncCommand(
            remote_user_host="user@host",
            push=True,
            pull=False,
            force=False,
            file_patterns=[
                DummyPattern(push=True, rsync_args=["pusharg"]),
                DummyPattern(pull=True, rsync_args=["pullarg"]),
                DummyPattern(push=True, pull=True, rsync_args=["botharg"]),
            ],
            source="/src/",
            dest="/dst/",
        )
        self.assertIn("rsync", cmd.args)
        self.assertIn("pusharg", cmd.args)
        self.assertNotIn("pullarg", cmd.args)
        self.assertIn("botharg", cmd.args)
        self.assertEqual(cmd.args[-2:], ["/src/", "user@host:/dst/"])

    def test_build_pull(self):
        cmd = RsyncCommand(
            remote_user_host="user@host",
            push=False,
            pull=True,
            force=False,
            file_patterns=[
                DummyPattern(push=True, rsync_args=["pusharg"]),
                DummyPattern(pull=True, rsync_args=["pullarg"]),
                DummyPattern(push=True, pull=True, rsync_args=["botharg"]),
            ],
            source="/src/",
            dest="/dst/",
        )
        self.assertIn("rsync", cmd.args)
        self.assertNotIn("pusharg", cmd.args)
        self.assertIn("pullarg", cmd.args)
        self.assertIn("botharg", cmd.args)
        self.assertEqual(cmd.args[-2:], ["user@host:/src/", "/dst/"])

    def test_build_force(self):
        cmd = RsyncCommand(
            remote_user_host="user@host",
            push=True,
            pull=False,
            force=True,
            file_patterns=[],
            source="/src/",
            dest="/dst/",
        )
        self.assertNotIn("--exclude=*", cmd.args)

    def test_build_noforce(self):
        cmd = RsyncCommand(
            remote_user_host="user@host",
            push=True,
            pull=False,
            force=False,
            file_patterns=[],
            source="/src/",
            dest="/dst/",
        )
        self.assertIn("--exclude=*", cmd.args)

    def test_build_multiple_pushargs(self):
        cmd = RsyncCommand(
            remote_user_host="user@host",
            push=True,
            pull=False,
            force=False,
            file_patterns=[
                DummyPattern(push=True, rsync_args=["pushargA1", "pushargA2"]),
                DummyPattern(push=True, rsync_args=["pushargB1"]),
                DummyPattern(pull=True, rsync_args=["pullarg"]),
                DummyPattern(push=True, pull=True, rsync_args=["botharg"]),
            ],
            source="/src/",
            dest="/dst/",
        )
        self.assertIn("rsync", cmd.args)
        self.assertIn("pushargA1", cmd.args)
        self.assertIn("pushargA2", cmd.args)
        self.assertIn("pushargB1", cmd.args)
        self.assertNotIn("pullarg", cmd.args)
        self.assertIn("botharg", cmd.args)
        self.assertEqual(cmd.args[-2:], ["/src/", "user@host:/dst/"])

    def test_build_with_dryrun(self):
        cmd = RsyncCommand(
            remote_user_host="user@host",
            push=True,
            pull=False,
            force=False,
            file_patterns=[],
            source="/src/",
            dest="/dst/",
            dry_run=True,
        )
        self.assertIn("rsync", cmd.args)
        self.assertIn("--recursive", cmd.args)
        self.assertIn("--dry-run", cmd.args)

    def test_build_without_dryrun(self):
        cmd = RsyncCommand(
            remote_user_host="user@host",
            push=True,
            pull=False,
            force=False,
            file_patterns=[],
            source="/src/",
            dest="/dst/",
        )
        self.assertIn("rsync", cmd.args)
        self.assertIn("--recursive", cmd.args)
        self.assertNotIn("--dry-run", cmd.args)
