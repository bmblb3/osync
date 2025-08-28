import unittest

from . import cli


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
        self.assertTrue(args.push)
        self.assertEqual(args.path, "foo/bar")

    def test_noforce_argument(self):
        args = cli.main(["--push", "foo/bar"])
        self.assertFalse(args.force)
        self.assertTrue(args.push)
        self.assertEqual(args.path, "foo/bar")

    def test_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            _ = cli.main(["--push", "--pull", "foo"])

    def test_neither_in_group(self):
        with self.assertRaises(SystemExit):
            _ = cli.main(["foo"])
