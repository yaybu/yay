import unittest
from yay.nodes.boxed import Boxed

class TestResolver(unittest.TestCase):
    pass

class Old:
    def test_string(self):
        r = Resolver({
            "foo": "123",
            "baz": "{foo}",
            }).resolve()

        self.failUnlessEqual(r["baz"], "123")

    def test_list(self):
        r = Resolver({
            "foo": "123",
            "baz": [
                "456",
                "{foo}",
                ],
            }).resolve()

        self.failUnlessEqual(r['baz'], ["456", "123"])

    def test_nested_dict(self):
        r = Resolver({
            "foo": 123,
            "baz": {
                "foo": "{foo}",
                },
            }).resolve()

        self.failUnlessEqual(r['baz']['foo'], "123")

    def test_cycle_detection(self):
        r = Resolver({
            "foo": "{baz}",
            "baz": "{foo}",
            })

        self.failUnlessRaises(ValueError, r.resolve)

