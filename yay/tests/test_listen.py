import unittest2
from .base import parse, resolve, TestCase
from yay import errors, ast
from yay.parser import ParseError
import mock


def parse_and_listen(data):
    g = parse(data)
    g.start_listening()
    return g


class TestObservation(unittest2.TestCase):

    def test_dict_parent(self):
        g = parse_and_listen("""
            parent:
                child:
                    a: 1
                    b: 2
                    c: 3
            """)
        trap = mock.Mock()
        g.get_key("parent").subscribe(trap)
        g.get_key("parent").get_key("child").get_key("a").changed()
        trap.assert_called_with()

    def test_expression(self):
        g = parse_and_listen("""
            example: {{ 1 + 2 }}
            """)
        trap = mock.Mock()
        g.get_key("example").subscribe(trap)
        g.get_key("example").lhs.changed()
        trap.assert_called_with()

    def test_identifier(self):
        g = parse_and_listen("""
            template: {{ var_that_changes }}
            var_that_changes: 1
            """)
        trap = mock.Mock()
        g.get_key("template").subscribe(trap)
        g.get_key("var_that_changes").changed()
        trap.assert_called_with()

