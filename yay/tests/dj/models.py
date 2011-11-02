from django.db import models


class Car(models.Model):
    name = models.CharField(max_length=256, primary_key=True)

class Part(models.Model):
    name = models.CharField(max_length=256, primary_key=True)
    car = models.ForeignKey(Car, related_name='parts')

