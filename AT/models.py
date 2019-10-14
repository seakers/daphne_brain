from django.db import models

class ECLSSAnomalies(models.Model):
    anomaly_id = models.IntegerField()
    description = models.CharField(max_length=200)

class ECLSSActions(models.Model):
    action_id = models.IntegerField()
    action = models.CharField(max_length=200)

class ECLSSCause(models.Model):
    cause_id = models.IntegerField()
    cause = models.CharField(max_length=200)

class ECLSSRelatedComponents(models.Model):
    component_id = models.IntegerField()
    component = models.CharField(max_length=200)

class ECLSSRisk(models.Model):
    risk_id = models.IntegerField()
    risk = models.CharField(max_length=200)
