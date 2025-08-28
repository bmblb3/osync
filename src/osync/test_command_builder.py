import os
import unittest
from typing import override
from unittest.mock import patch

from .command_builder import RsyncCommand
from .file_pattern import FilePattern


class DummyPattern(FilePattern):
    def __init__(
        self,
        push: bool = False,
        pull: bool = False,
        rsync_args: list[str] | None = None,
    ):
        super().__init__(desc="", patterns=[""])
        self.push: bool = push
        self.pull: bool = pull
        self._rsync_args: list[str] = rsync_args or []

    @override
    def rsync_args(self):
        return self._rsync_args


class TestRsyncCommand(unittest.TestCase):
    def test_env_var(self):
        with patch.dict(os.environ, {"OSYNC_REMOTE_USER_HOST": "test_value"}):
            assert os.environ["OSYNC_REMOTE_USER_HOST"] == "test_value"
            cmd = RsyncCommand(
                push=True,
                pull=False,
                force=False,
                file_patterns=[],
            )
            self.assertEqual("test_value", cmd.remote_user_host)

    def test_raises_error_when_no_env_var(self):
        with self.assertRaisesRegex(ValueError, "(E|e)nvironment (V|v)ariable"):
            _ = RsyncCommand(
                push=True,
                pull=False,
                force=False,
                file_patterns=[],
            )

    def test_build_has_base_args(self):
        cmd = RsyncCommand(
            remote_user_host="user@host",
            push=True,
            pull=False,
            force=False,
            file_patterns=[],
        )
        args = cmd.build("/src/", "/dst/")
        self.assertIn("rsync", args)
        self.assertIn("--recursive", args)

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
        )
        args = cmd.build("/src/", "/dst/")
        self.assertIn("rsync", args)
        self.assertIn("pusharg", args)
        self.assertNotIn("pullarg", args)
        self.assertIn("botharg", args)
        self.assertEqual(args[-2:], ["/src/", "user@host:/dst/"])

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
        )
        args = cmd.build("/src/", "/dst/")
        self.assertIn("rsync", args)
        self.assertNotIn("pusharg", args)
        self.assertIn("pullarg", args)
        self.assertIn("botharg", args)
        self.assertEqual(args[-2:], ["user@host:/src/", "/dst/"])

    def test_build_force(self):
        cmd = RsyncCommand(
            remote_user_host="user@host",
            push=True,
            pull=False,
            force=True,
            file_patterns=[],
        )
        args = cmd.build("/src/", "/dst/")
        self.assertNotIn("--exclude=*", args)

    def test_build_noforce(self):
        cmd = RsyncCommand(
            remote_user_host="user@host",
            push=True,
            pull=False,
            force=False,
            file_patterns=[],
        )
        args = cmd.build("/src/", "/dst/")
        self.assertIn("--exclude=*", args)

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
        )
        args = cmd.build("/src/", "/dst/")
        self.assertIn("rsync", args)
        self.assertIn("pushargA1", args)
        self.assertIn("pushargA2", args)
        self.assertIn("pushargB1", args)
        self.assertNotIn("pullarg", args)
        self.assertIn("botharg", args)
        self.assertEqual(args[-2:], ["/src/", "user@host:/dst/"])
