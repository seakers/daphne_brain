from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.db import models
from merge_session.merge_db import MergeSession


# General user information class
class UserInformation(models.Model):
    # Primary key tuple
    session = models.ForeignKey(MergeSession, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    # Daphne Version Choice
    DAPHNE_VERSIONS = (
        ('EOSS', 'Earth Observation Satellite Systems'),
        ('EDL', 'Entry, Descent & Landing'),
        ('AnomalyDetection', 'Anomaly Detection for Astronauts'),
    )
    daphne_version = models.CharField(max_length=40, choices=DAPHNE_VERSIONS)

    # Websockets communication
    channel_name = models.CharField(max_length=120)

    # Special restrictions
    class Meta:
        unique_together = ("session", "user")


# Context for EOSS Users
class EOSSContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)
    problem = models.CharField(max_length=50)
    dataset_name = models.CharField(max_length=80)

    # Properties related to the dataset, the list of designs comes from the Design model
    last_arch_id = models.IntegerField()
    selected_arch_id = models.IntegerField()

    # Counter for manually added designs
    added_archs_count = models.IntegerField()

    vassar_port = models.IntegerField()


# Context for Active Parts of Daphne
class ActiveContext(models.Model):
    eosscontext = models.OneToOneField(EOSSContext, on_delete=models.CASCADE)

    # Settings for the Active Context
    show_background_search_feedback = models.BooleanField(default=False)
    check_for_diversity = models.BooleanField(default=True)
    show_arch_suggestions = models.BooleanField(default=True)

    # The list of designs in the queue is contained in model Design


class EngineerContext(models.Model):
    eosscontext = models.OneToOneField(EOSSContext, on_delete=models.CASCADE)

    # Context that is used for those questions related with the engineer skill
    vassar_instrument = models.TextField()
    instrument_parameter = models.TextField()
    vassar_measurement = models.TextField()


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


# An answer from Daphne
class Answer(models.Model):
    eosscontext = models.ForeignKey(EOSSContext, on_delete=models.CASCADE)
    voice_answer = models.TextField()
    visual_answer_type = models.TextField()
    visual_answer = models.TextField()


# An allowed command for Daphne (to be used with experiments to limit functionalities programmatically
class AllowedCommand(models.Model):
    eosscontext = models.ForeignKey(EOSSContext, on_delete=models.CASCADE)

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
