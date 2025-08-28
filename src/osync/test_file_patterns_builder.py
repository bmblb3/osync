import os
import tempfile
import unittest

import yaml

from .file_pattern import FilePattern
from .file_patterns_builder import FilePatterns


class TestFilePatternsBuilder(unittest.TestCase):
    def test_list_with_single_dict_builds_patterns(self):
        patterns_dicts = [
            {
                "desc": "desc1",
                "patterns": ["p1"],
                "push": True,
                "pull": True,
            },
        ]
        patterns = FilePatterns.from_file_patterns(patterns_dicts)
        self.assertEqual(len(patterns), 1)
        self.assertIsInstance(patterns[0], FilePattern)
        self.assertEqual(patterns[0].desc, "desc1")
        self.assertEqual(patterns[0].patterns, ["p1"])
        self.assertEqual(patterns[0].push, True)
        self.assertEqual(patterns[0].pull, True)

    def test_multiple_dicts_builds_patterns(self):
        patterns_dicts = [
            {
                "desc": "desc1",
                "patterns": ["p1"],
                "push": True,
                "pull": True,
            },
            {
                "desc": "desc2",
                "patterns": ["p2A", "p2B"],
                "push": False,
                "pull": False,
            },
        ]
        patterns = FilePatterns.from_file_patterns(patterns_dicts)
        self.assertEqual(len(patterns), 2)
        self.assertEqual(patterns[0].desc, "desc1")
        self.assertEqual(patterns[0].patterns, ["p1"])
        self.assertEqual(patterns[0].push, True)
        self.assertEqual(patterns[0].pull, True)
        self.assertEqual(patterns[1].desc, "desc2")
        self.assertEqual(patterns[1].patterns, ["p2A", "p2B"])
        self.assertEqual(patterns[1].push, False)
        self.assertEqual(patterns[1].pull, False)

    def test_build_from_file(self):
        patterns_data = [
            {
                "desc": "desc1",
                "patterns": ["p1"],
                "push": True,
                "pull": True,
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(patterns_data, f)
            temp_file = f.name

        try:
            patterns = FilePatterns.from_yml(temp_file)
            self.assertEqual(len(patterns), 1)
            self.assertIsInstance(patterns[0], FilePattern)
            self.assertEqual(patterns[0].desc, "desc1")
            self.assertEqual(patterns[0].patterns, ["p1"])
            self.assertEqual(patterns[0].push, True)
            self.assertEqual(patterns[0].pull, True)
        finally:
            os.unlink(temp_file)
