from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.db import models
from .utils import generate_mycroft_session

import random
import string

# General user information class
from rest_framework import serializers

from EOSS.aws.utils import get_boto3_client


def get_eval_request_queue():
    sqs_client = get_boto3_client('sqs')
    queue_name = 'eval-request-queue-' + str(''.join(random.choices(string.ascii_uppercase + string.digits, k=15)))
    list_response = sqs_client.list_queues()
    if 'QueueUrls' in list_response:
        queue_names = [url.split("/")[-1] for url in list_response['QueueUrls']]
        if queue_name in queue_names:
            queue_url_idx = queue_names.index(queue_name)
            queue_url = list_response['QueueUrls'][queue_url_idx]
            sqs_client.purge_queue(QueueUrl=queue_url)
            return queue_url
        else:
            return sqs_client.create_queue(QueueName=queue_name)['QueueUrl']
    return None

def get_eval_response_queue():
    sqs_client = get_boto3_client('sqs')
    queue_name = 'eval-response-queue-' + str(''.join(random.choices(string.ascii_uppercase + string.digits, k=15)))
    list_response = sqs_client.list_queues()
    if 'QueueUrls' in list_response:
        queue_names = [url.split("/")[-1] for url in list_response['QueueUrls']]
        if queue_name in queue_names:
            queue_url_idx = queue_names.index(queue_name)
            queue_url = list_response['QueueUrls'][queue_url_idx]
            sqs_client.purge_queue(QueueUrl=queue_url)
            return queue_url
        else:
            return sqs_client.create_queue(QueueName=queue_name)['QueueUrl']
    return None



class MycroftUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    # Mycroft Code
    mycroft_session = models.CharField(max_length=9, unique=False, default=generate_mycroft_session, null=True)  # four digit session number


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

    # Mycroft information
    # mycroft_session = models.CharField(max_length=9, unique=False, default=generate_mycroft_session)  # four digit session number
    mycroft_connection = models.BooleanField(default=False)                                           # true if connection established
    mycroft_channel_name = models.CharField(max_length=120, null=True)                                # channel name for talking to Mycroft

    # User eval request queue created at user account creation
    eval_request_queue = models.TextField(null=True, default=get_eval_request_queue)
    eval_response_queue = models.TextField(null=True, default=get_eval_response_queue)


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
    dwriter = models.CharField(max_length=40, choices=WRITERS)
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
