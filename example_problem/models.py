from django.db import models
from rest_framework import serializers

from daphne_context.models import UserInformation, DialogueContext


# Context for Example Users
class ExampleContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)
    problem = models.CharField(max_length=50)
    dataset_name = models.CharField(max_length=80)
    dataset_user = models.BooleanField()

    # Properties related to the dataset, the list of designs comes from the Design model
    last_arch_id = models.IntegerField()
    selected_arch_id = models.IntegerField()

    # Counter for manually added designs
    added_archs_count = models.IntegerField()


class ExampleContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleContext
        fields = '__all__'


class ExampleDialogueContext(models.Model):
    dialoguecontext = models.OneToOneField(DialogueContext, on_delete=models.CASCADE)


class ExampleDialogueContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleDialogueContext
        fields = '__all__'


class EngineerContext(models.Model):
    eossdialoguecontext = models.OneToOneField(ExampleDialogueContext, on_delete=models.CASCADE)

    # Context that is used for those questions related with the engineer skill
    


class EngineerContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineerContext
        fields = '__all__'


# A design can be part of either a dataset in the examplecontext or a queue for the active background search
class Design(models.Model):
    design_id = models.AutoField(primary_key=True)

    examplecontext = models.ForeignKey(ExampleContext, on_delete=models.CASCADE, null=True)

    id = models.IntegerField()
    inputs = models.TextField()
    outputs = models.TextField()

    # Special restrictions
    class Meta:
        unique_together = ("examplecontext", "id")
