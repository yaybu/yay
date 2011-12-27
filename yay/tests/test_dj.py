
from django.conf import settings
settings.configure(
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            },
        },
    INSTALLED_APPS=['yay.tests.dj'],
    TIME_ZONE = 'Europe/London',
    )

from unittest import TestCase

from yay.config import Config
from yay.tests.dj.models import Car, Part
from yay.nodes import BoxingFactory
from yay.nodes.datastore import dj
from django.core.management.commands.syncdb import Command as syncdb


class TestDjangoBase(TestCase):

    def setUp(self):
        syncdb().handle_noargs()

        c1 = Car(name="fred")
        c1.save()
        c2 = Car(name="bobby")
        c2.save()

        p1 = Part(name="wheel", car=c1)
        p1.save()
        p2 = Part(name="brake", car=c1)
        p2.save()
        p3 = Part(name="badger", car=c2)
        p3.save()


class TestDjangoBoxing(TestDjangoBase):

    def test_box_instance(self):
        b = BoxingFactory.box(Car(name="pudding"))
        self.assert_(isinstance(b, dj.Instance))

    def test_box_query(self):
        b = BoxingFactory.box(Car.objects.filter(name="pudding"))
        self.assert_(isinstance(b, dj.InstanceList))

    def test_box_manager(self):
        b = BoxingFactory.box(Car.objects)
        self.assert_(isinstance(b, dj.InstanceList))


class TestDjangoYay(TestDjangoBase):

    def setUp(self):
        TestDjangoBase.setUp(self)

        self.config = Config()
        self.config.load("""
            metadata.bind:
                type: djangostore
                model: yay.tests.dj.models
            """)

    def test_all_cars(self):
        self.config.load("""test: ${metadata.Car}""")
        l = self.config.get()["test"]

        self.failUnless(isinstance(l[0], dict))
        self.failUnlessEqual(l[0]["name"], "fred")

    def test_foreach_car(self):
        self.config.load("""
            test.foreach c in metadata.Car: ${c.name}
            """)

        self.failUnlessEqual(self.config.get()["test"], ["fred", "bobby"])

    def test_foreach_car_parts(self):
        self.config.load("""
            test.foreach c in metadata.Car:
              .foreach p in c.parts: ${p.name}
            """)

        self.failUnlessEqual(self.config.get()["test"], ['wheel', 'brake', 'badger'])

    def test_foreach_car_parts_if(self):
        self.config.load("""
            x: badger
            test.foreach c in metadata.Car:
              .foreach p in c.parts if p.name=x: ${p.name}
            """)

        self.failUnlessEqual(self.config.get()["test"], ["badger"])

    def test_foreach_car_parts_if_failing(self):
        self.config.load("""
            x: badge
            test.foreach c in metadata.Car:
              .foreach p in c.parts if p.name=x: ${p.name}
            """)

        self.failUnlessEqual(self.config.get()["test"], [])

    def test_model_callable(self):
        self.config.load("""
            test.foreach p in metadata.Car.some_callable: ${p.name}
            """)

        self.failUnlessEqual(self.config.get()["test"], ['wheel','brake','badger'])

    def test_model_callable_generator(self):
        self.config.load("""
            test.foreach p in metadata.Car.some_generator: ${p.name}
            """)

        self.failUnlessEqual(self.config.get()["test"], ['wheel','brake','badger'])

