import os
import shutil
import tempfile
import unittest
from typing import override

from .findup import findup


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
