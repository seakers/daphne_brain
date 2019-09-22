from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.db import models


# General user information class
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


# An answer from Daphne
class Answer(models.Model):
    user_information = models.ForeignKey(UserInformation, on_delete=models.CASCADE)
    voice_answer = models.TextField()
    visual_answer_type = models.TextField()
    visual_answer = models.TextField()


# Experiment Context (to perform experiments with human subjects and Daphne)
class ExperimentContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)

    is_running = models.BooleanField()
    experiment_id = models.IntegerField()
    current_state = models.TextField()


# A data structure defining an experimental stage
class ExperimentStage(models.Model):
    experimentcontext = models.ForeignKey(ExperimentContext, on_delete=models.CASCADE)

    type = models.CharField(max_length=50)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    end_state = models.TextField()


class ExperimentAction(models.Model):
    experimentstage = models.ForeignKey(ExperimentStage, on_delete=models.CASCADE)

    action = models.TextField()
    date = models.DateTimeField()


# An allowed command for Daphne (to be used with experiments to limit functionalities programmatically)
class AllowedCommand(models.Model):
    user_information = models.ForeignKey(UserInformation, on_delete=models.CASCADE)

    # Command Type Choice
    COMMAND_TYPES = (
        ('engineer', 'Engineer Commands'),
        ('critic', 'Critic Commands'),
        ('historian', 'Historian Commands'),
        ('analyst', 'iFEED Commands'),
        ('analyst_instruments', 'Instruments Cheatsheet'),
        ('analyst_instrument_parameters', 'Instrument Parameters Cheatsheet'),
        ('analyst_measurements', 'Measurements Cheatsheet'),
        ('analyst_stakeholders', 'Stakeholders Cheatsheet'),
        ('measurements', 'Historical Measurements Cheatsheet'),
        ('missions', 'Historical Missions Cheatsheet'),
        ('technologies', 'Historical Technologies Cheatsheet'),
        ('objectives', 'Objectives Cheatsheet'),
        ('space_agencies', 'Space Agencies Cheatsheet'),

    )
    command_type = models.CharField(max_length=40, choices=COMMAND_TYPES)

    # Command number
    command_descriptor = models.IntegerField()
