from django.db import models

from daphne_context.models import UserInformation


class EDLContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)

    current_mat_file = models.CharField(max_length=255)
    current_mat_file_for_print = models.CharField(max_length=255)
    current_scorecard_file = models.CharField(max_length=255)
    current_scorecard = models.CharField(max_length=255)
