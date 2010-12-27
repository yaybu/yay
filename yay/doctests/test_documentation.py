
import unittest
import doctest

from yay.config import Config
from yay.openers import MemOpener

class TestConfig(Config):

    def file(self, uri, data):
        MemOpener.add(uri, data)

documentation = [
    'extends.rst',
    'actions.rst',
    ]

globs = {
    "config": TestConfig(),
}


class TestDocumentation(unittest.TestCase):

    def __new__(self, test):
        return getattr(self, test)()

    @classmethod
    def test_documentation(cls):
        return doctest.DocFileSuite(
            *documentation,
            globs = globs
        )

