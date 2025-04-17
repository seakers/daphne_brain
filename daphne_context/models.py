from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.db import models


# General user information class
from rest_framework import serializers


class UserInformation(models.Model):
    # Primary key tuple
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    # Daphne Version Choice
    DAPHNE_VERSIONS = (
        ('EOSS', 'Earth Observation Satellite Systems'),
        ('EDL', 'Entry, Descent & Landing'),
        ('AT', 'Anomaly Detection for Astronauts'),
    )
    daphne_version = models.CharField(max_length=40, choices=DAPHNE_VERSIONS)

    # Websockets communication
    channel_name = models.CharField(max_length=120)

    # Special restrictions
    class Meta:
        unique_together = ("session", "user")


# Daphne conversations
class DialogueHistory(models.Model):
    user_information = models.ForeignKey(UserInformation, on_delete=models.CASCADE)

    voice_message = models.TextField()
    visual_message_type = models.TextField()
    visual_message = models.TextField()

    WRITERS = (
        ('user', 'Human'),
        ('daphne', 'Machine'),
    )
    writer = models.CharField(max_length=40, choices=WRITERS)
    date = models.DateTimeField()


class DialogueContext(models.Model):
    dialogue_history = models.OneToOneField(DialogueHistory, on_delete=models.CASCADE)

    is_clarifying_input = models.BooleanField()
    clarifying_role = models.IntegerField(null=True)
    clarifying_commands = models.TextField(null=True)


class DialogueContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = DialogueContext
        fields = '__all__'
