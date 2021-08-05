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

    # Current telemetry values context variable
    current_telemetry_values = models.TextField(default='')

    # Thread deployment status bool
    are_at_threads_deployed = models.BooleanField(default=False)

    # Thread deployment status bool
    seen_tutorial = models.BooleanField(default=False)


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


class ATDialogueContext(models.Model):
    dialoguecontext = models.OneToOneField(DialogueContext, on_delete=models.CASCADE)

    # All, Current, Next and Previous procedural steps
    all_steps_from_procedure = models.TextField(default='')
    next_step_pointer = models.IntegerField(default=-1)
    previous_step_pointer = models.IntegerField(default=-1)
    current_step_pointer = models.IntegerField(default=-1)


class ATDialogueContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ATDialogueContext
        fields = '__all__'
