
from django.conf import settings
settings.configure(
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            },
        },
    TIME_ZONE = 'Europe/London',
    )

from django.db import models
import yay
import StringIO
from unittest import TestCase


class Car(models.Model):
    name = models.CharField(max_length=256, primary_key=True)

class Part(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    car = models.ForeignKey(Car, related_name='parts')


class TestDjango(TestCase):

   def test_hello(self):
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

       print Car.objects.all()
       print Part.objects.all()

