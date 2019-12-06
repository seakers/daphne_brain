from django.db import models
from rest_framework import serializers

from daphne_context.models import UserInformation, DialogueContext


# Context for EOSS Users
class EOSSContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)
    problem = models.CharField(max_length=50)
    dataset_name = models.CharField(max_length=80)
    dataset_user = models.BooleanField()

    # Properties related to the dataset, the list of designs comes from the Design model
    last_arch_id = models.IntegerField()
    selected_arch_id = models.IntegerField()

    # Counter for manually added designs
    added_archs_count = models.IntegerField()

    # Backends information
    vassar_port = models.IntegerField()
    ga_id = models.TextField(null=True)


class EOSSContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = EOSSContext
        fields = '__all__'


# Context for Active Parts of Daphne
class ActiveContext(models.Model):
    eosscontext = models.OneToOneField(EOSSContext, on_delete=models.CASCADE)

    # Settings for the Active Context
    show_background_search_feedback = models.BooleanField(default=False)
    check_for_diversity = models.BooleanField(default=True)
    show_arch_suggestions = models.BooleanField(default=True)

    # The list of designs in the queue is contained in model Design


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


# A design can be part of either a dataset in the EOSSContext or a queue for the active background search
class Design(models.Model):
    design_id = models.AutoField(primary_key=True)

    eosscontext = models.ForeignKey(EOSSContext, on_delete=models.CASCADE, null=True)
    activecontext = models.ForeignKey(ActiveContext, on_delete=models.CASCADE, null=True)

    id = models.IntegerField()
    inputs = models.TextField()
    outputs = models.TextField()

    # Special restrictions
    class Meta:
        unique_together = ("eosscontext", "activecontext", "id")
