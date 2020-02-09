from django.db import models
from rest_framework import serializers

from daphne_context.models import UserInformation, DialogueContext


# Context for AT Users
class ATContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)

    current_anomaly = models.CharField(max_length=80)
    current_step = models.IntegerField()
    current_telemetry_values = models.TextField(default='')
    current_telemetry_info = models.TextField(default='')


class ATContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ATContext
        fields = '__all__'


# Context for Active Parts of Daphne
class ActiveATContext(models.Model):
    atcontext = models.OneToOneField(ATContext, on_delete=models.CASCADE)


class ActiveContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveATContext
        fields = '__all__'
