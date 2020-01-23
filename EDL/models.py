from django.db import models

from daphne_context.models import UserInformation


class EDLContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)

    current_mat_file = models.CharField(max_length=255)
    current_mat_file_for_print = models.CharField(max_length=255)
    current_scorecard_file = models.CharField(max_length=255)
    current_scorecard_path = models.CharField(max_length=255)
    selected_case = models.IntegerField()
    current_mission = models.CharField(max_length=255)
    current_metrics_of_interest = models.TextField(null=True)
    current_cormat_df = models.BinaryField(max_length=None, default=bytes())
    current_cormat_status = models.CharField(max_length=255, default="false")


class EDLContextScorecards(models.Model):
    scorecard_name = models.CharField(max_length=225, default="")
    current_scorecard_path = models.CharField(max_length=255, default="")
    current_scorecard_df = models.BinaryField(max_length=None, default=bytes())
    current_scorecard_df_flag = models.BinaryField(max_length=None, default=bytes())
    current_scorecard_df_fail = models.BinaryField(max_length=None, default=bytes())
    current_scorecard_df_db = models.BinaryField(max_length=None, default=bytes())
    edl_context = models.ForeignKey(EDLContext, on_delete=models.CASCADE)
    current_corr_mat_df = models.BinaryField(max_length=None, default=bytes())
    current_corr_mat_status = models.CharField(max_length=255, default="false")
