import unittest

from .file_pattern import FilePattern


class TestFilePattern(unittest.TestCase):
    def test_multiple_patterns(self):
        fp = FilePattern(
            desc="Test patterns", patterns=["*.txt", "*.md"], push=True, pull=False
        )
        expected = ["--include=*.txt", "--include=*.md"]
        self.assertEqual(fp.rsync_args(), expected)

    def test_single_pattern(self):
        fp = FilePattern(
            desc="Single pattern", patterns=["*.py"], push=False, pull=True
        )
        expected = ["--include=*.py"]
        self.assertEqual(fp.rsync_args(), expected)

    def test_no_patterns(self):
        fp = FilePattern(desc="No patterns", patterns=[], push=False, pull=False)
        with self.assertRaisesRegex(ValueError, "Patterns list.*empty"):
            _ = fp.rsync_args()

    def test_from_dict(self):
        fp = FilePattern.from_dict(
            {"desc": "No patterns", "patterns": ["*.py"], "push": False, "pull": False}
        )
        expected = ["--include=*.py"]
        self.assertEqual(fp.rsync_args(), expected)
