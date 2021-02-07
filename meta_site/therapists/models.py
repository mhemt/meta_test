from django.db import models


class Therapist(models.Model):
    name = models.CharField(max_length=100)
    photo_url = models.CharField(max_length=300)

    class Meta:
        db_table = 'therapists'
        ordering = ['id']


class Method(models.Model):
    name = models.CharField(max_length=30)
    therapists = models.ManyToManyField(Therapist, related_name='methods', db_table='therapists_methods')

    class Meta:
        db_table = 'methods'
