from django.db import models
from rest_framework import serializers

from daphne_context.models import UserInformation, DialogueContext


# Context for AT Users
class ATContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)

    current_anomaly = models.CharField(max_length=80)
    current_step = models.IntegerField()


class ATContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ATContext
        fields = '__all__'
