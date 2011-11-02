from django.db import models


class Car(models.Model):
    name = models.CharField(max_length=256, primary_key=True)

    @classmethod
    def some_callable(cls):
        return list(Part.objects.all())

    @classmethod
    def some_generator(cls):
        for p in Part.objects.all():
            yield p

class Part(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    car = models.ForeignKey(Car, related_name='parts')

