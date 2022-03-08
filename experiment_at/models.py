from django.db import models

# Experiment Context (to perform experiments with human subjects and Daphne)
from daphne_context.models import UserInformation


class ATExperimentContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)

    is_running = models.BooleanField()
    experiment_id = models.IntegerField()
    current_state = models.TextField()


# A data structure defining an experimental stage
class ATExperimentStage(models.Model):
    atexperimentcontext = models.ForeignKey(ATExperimentContext, on_delete=models.CASCADE)

    type = models.CharField(max_length=50)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    end_state = models.TextField()


class ATExperimentAction(models.Model):
    atexperimentstage = models.ForeignKey(ATExperimentStage, on_delete=models.CASCADE)

    action = models.TextField()
    date = models.DateTimeField()


# An allowed command for Daphne (to be used with experiments to limit functionalities programmatically)
class ATAllowedCommand(models.Model):
    user_information = models.ForeignKey(UserInformation, on_delete=models.CASCADE)

    # Command Type Choice
    COMMAND_TYPES = (
        ('detection', 'Detection Commands'),
        ('diagnosis', 'Diagnosis Commands'),
        ('recommendation', 'Recommendation Commands'),
    )
    command_type = models.CharField(max_length=40, choices=COMMAND_TYPES)

    # Command number
    command_descriptor = models.IntegerField()
