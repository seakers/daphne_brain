from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from daphne_context.models import UserInformation
from django.db import models



# --> many-to-one relationship with UserInformation
# class ArchitecturesClicked(models.Model):
#     user_information = models.ForeignKey(UserInformation, on_delete=models.CASCADE)
#     arch_clicked = models.TextField(max_length=500)
#
# class ArchitecturesUpdated(models.Model):
#     user_information = models.ForeignKey(UserInformation, on_delete=models.CASCADE)
#     arch_updated = models.TextField(max_length=500)
#
# class ArchitecturesEvaluated(models.Model):
#     user_information = models.ForeignKey(UserInformation, on_delete=models.CASCADE)
#     arch_evaluated = models.TextField(max_length=500)

