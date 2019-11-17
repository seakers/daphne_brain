from django.db import models

# Experiment Context (to perform experiments with human subjects and Daphne)
from daphne_context.models import UserInformation


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
        ('analyst', 'iFEED Commands'),
        ('explorer', 'Explorer Commands'),
        ('historian', 'Historian Commands'),
        ('critic', 'Critic Commands'),
        ('engineer_instruments', 'Instruments Cheatsheet'),
        ('engineer_instrument_parameters', 'Instrument Parameters Cheatsheet'),
        ('engineer_measurements', 'Measurements Cheatsheet'),
        ('engineer_stakeholders', 'Stakeholders Cheatsheet'),
        ('engineer_objectives', 'Objectives Cheatsheet'),
        ('engineer_subobjectives', 'Subobjectives Cheatsheet'),
        ('historian_measurements', 'Historical Measurements Cheatsheet'),
        ('historian_missions', 'Historical Missions Cheatsheet'),
        ('historian_technologies', 'Historical Technologies Cheatsheet'),
        ('historian_space_agencies', 'Space Agencies Cheatsheet'),

    )
    command_type = models.CharField(max_length=40, choices=COMMAND_TYPES)

    # Command number
    command_descriptor = models.IntegerField()
