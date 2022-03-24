from django.db import models
from rest_framework import serializers

from daphne_context.models import UserInformation, DialogueContext


# Context for EOSS Users
class EOSSContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)

    # Properties related to the dataset, the list of designs comes from the Design model
    last_arch_id = models.IntegerField()
    selected_arch_id = models.IntegerField()

    # Problem and dataset settings for current user
    group_id = models.IntegerField(default=1)
    problem_id = models.IntegerField(default=1)
    dataset_id = models.IntegerField()

    # Counter for manually added designs
    added_archs_count = models.IntegerField()

    # Backends information
    vassar_request_queue_url = models.TextField(null=True)
    vassar_response_queue_url = models.TextField(null=True)
    vassar_information = models.JSONField(default=dict)
    ga_request_queue_url = models.TextField(null=True)
    ga_response_queue_url = models.TextField(null=True)
    ga_information = models.JSONField(default=dict)
    ga_thread_id = models.IntegerField(default=-1)


class EOSSContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = EOSSContext
        fields = '__all__'


# Context for Active Parts of Daphne
class ActiveContext(models.Model):
    eosscontext = models.OneToOneField(EOSSContext, on_delete=models.CASCADE)

    # Settings for the Proactive Feedback
    check_for_diversity = models.BooleanField(default=True)

    show_engineer_suggestions = models.BooleanField(default=True)
    engineer_suggestions_frequency = models.IntegerField(default=3) # 3 modifications/minute
    
    show_historian_suggestions = models.BooleanField(default=True)
    historian_suggestions_frequency = models.IntegerField(default=3) # 3 modifications/minute

    show_analyst_suggestions = models.BooleanField(default=True)
    analyst_suggestions_frequency = models.BooleanField(default=45) # 1 notif/45s


class ActiveContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveContext
        fields = '__all__'


class EOSSDialogueContext(models.Model):
    dialoguecontext = models.OneToOneField(DialogueContext, on_delete=models.CASCADE)


class EOSSDialogueContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = EOSSDialogueContext
        fields = '__all__'


class EngineerContext(models.Model):
    eossdialoguecontext = models.OneToOneField(EOSSDialogueContext, on_delete=models.CASCADE)

    # Context that is used for those questions related with the engineer skill
    vassar_instrument = models.TextField(null=True)
    instrument_parameter = models.TextField(null=True)
    vassar_measurement = models.TextField(null=True)


class EngineerContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineerContext
        fields = '__all__'
