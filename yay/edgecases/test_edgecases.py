
import unittest
import doctest
import os
import glob

from yay.config import Config
from yay.openers import MemOpener

class TestConfig(Config):

    def file(self, uri, data):
        MemOpener.add(uri, data)

documentation = [os.path.basename(x) for x in glob.glob(os.path.join(os.path.dirname(__file__), "*.rst"))]

globs = {
    "config": TestConfig(),
}


class TestEdgeCases(unittest.TestCase):

    def __new__(self, test):
        return getattr(self, test)()

    @classmethod
    def test_edge_case(cls):
        return doctest.DocFileSuite(
            *documentation,
            globs = globs
        )

