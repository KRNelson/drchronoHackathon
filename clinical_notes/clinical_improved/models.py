from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Patient(models.Model):
    name = models.CharField(max_length=100)

class Appointment(models.Model):
    patient_id = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date_time = models.DateTimeField()

class Template(models.Model):
    name = models.CharField(max_length=100)

class Field(models.Model):
    template_id = models.ForeignKey(Template, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

class Value(models.Model):
    patient_id = models.ForeignKey(Patient, on_delete=models.CASCADE)
    appointment_id = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    template_id = models.ForeignKey(Template, on_delete=models.CASCADE)
    field_id = models.ForeignKey(Field, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)
