from django.db import models
from rest_framework import serializers

from daphne_context.models import UserInformation, DialogueContext


# Context for AT Users
class ATContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)

    # In order to support object types, some of the following context variables are defined as TextFields. The variables
    # are then stored as a json string and parsed when required. Not optimal, could be done better in the future.

    # For the anomalies, measurements and procedures, a "selected" and "recent" context variable is defined. This allows
    # to ask questions such as "What are the risks of THIS anomaly?" from the chat box. A proper method is then defined
    # to retrieve the meaning of the "THIS" pointer.
    selected_anomalies = models.TextField(default='')
    selected_measurements = models.TextField(default='')
    selected_procedures = models.TextField(default='')

    # Current step context variable (dictionary with the selected procedures as keys and their current steps as values)
    current_procedure_step = models.TextField(default='')

    # Current telemetry values context variable
    current_telemetry_values = models.TextField(default='')


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
