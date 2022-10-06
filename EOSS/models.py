from django.db import models
from rest_framework import serializers

from asgiref.sync import async_to_sync

from daphne_context.models import UserInformation, DialogueContext

# Context for EOSS Users
class EOSSContext(models.Model):
    user_information = models.OneToOneField(UserInformation, on_delete=models.CASCADE)


    # Problem and dataset settings for current user
    group_id = models.IntegerField(default=1)
    problem_id = models.IntegerField(default=1)
    dataset_id = models.IntegerField()


    # Properties related to the dataset, the list of designs comes from the Design model
    last_arch_id = models.IntegerField()
    selected_arch_id = models.IntegerField()


    # Counter for manually added designs
    added_archs_count = models.IntegerField()


    # Backends information
    vassar_request_queue_url = models.TextField(null=True)
    vassar_response_queue_url = models.TextField(null=True)
    vassar_information = models.JSONField(default=dict)
    ga_request_queue_url = models.TextField(null=True)
    ga_response_queue_url = models.TextField(null=True)
    ga_information = models.JSONField(default=dict)
    ga_thread_id = models.IntegerField(default=-1)



    ########################
    ### AWS 2.0 Backends ###
    ########################

    # --> Locks
    service_lock = models.BooleanField(default=False)
    design_evaluator_service_lock = models.BooleanField(default=False)
    genetic_algorithm_service_lock = models.BooleanField(default=False)

    # --> Design Evaluator
    design_evaluator_instance_count = models.IntegerField(default=1)
    design_evaluator_request_queue_name = models.TextField(null=True)  # user-1-design-evaluator-request-queue
    design_evaluator_request_queue_url = models.TextField(null=True)
    design_evaluator_response_queue_name = models.TextField(null=True)  # user-1-design-evaluator-response-queue
    design_evaluator_response_queue_url = models.TextField(null=True)

    # --> Genetic Algorithm
    genetic_algorithm_instance_count = models.IntegerField(default=1)
    genetic_algorithm_request_queue_name = models.TextField(null=True)  # user-1-genetic-algorithm-request-queue
    genetic_algorithm_request_queue_url = models.TextField(null=True)
    genetic_algorithm_response_queue_name = models.TextField(null=True)  # user-1-genetic-algorithm-response-queue
    genetic_algorithm_response_queue_url = models.TextField(null=True)






    ##################
    ### Deprecated ###
    ##################

    cluster_name = models.TextField(default='daphne-dev-cluster')
    design_evaluator_task_count = models.IntegerField(default=1)
    genetic_algorithm_task_count = models.IntegerField(default=1)
    eval_request_queue_url = models.TextField(null=True)
    eval_response_queue_url = models.TextField(null=True)


class EvaluatorInstance(models.Model):
    eosscontext = models.ForeignKey(EOSSContext, on_delete=models.CASCADE)

    # Queues
    ping_request_queue_url = models.TextField(null=True)
    ping_response_queue_url = models.TextField(null=True)
    private_request_queue_url = models.TextField(null=True)
    private_response_queue_url = models.TextField(null=True)

    # AWS Resource
    arn = models.TextField(null=True)




class EOSSContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = EOSSContext
        fields = '__all__'


# Context for Active Parts of Daphne
class ActiveContext(models.Model):
    eosscontext = models.OneToOneField(EOSSContext, on_delete=models.CASCADE)

    # Settings for the Proactive Feedback
    check_for_diversity = models.BooleanField(default=False)

    show_engineer_suggestions = models.BooleanField(default=False)
    engineer_suggestions_frequency = models.IntegerField(default=3) # 3 modifications/minute
    
    show_historian_suggestions = models.BooleanField(default=False)
    historian_suggestions_frequency = models.IntegerField(default=3) # 3 modifications/minute

    show_analyst_suggestions = models.BooleanField(default=False)
    analyst_suggestions_frequency = models.IntegerField(default=45) # 1 notif/45s


class ActiveContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveContext
        fields = '__all__'


class EOSSDialogueContext(models.Model):
    dialoguecontext = models.OneToOneField(DialogueContext, on_delete=models.CASCADE)


class EOSSDialogueContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = EOSSDialogueContext
        fields = '__all__'


class EngineerContext(models.Model):
    eossdialoguecontext = models.OneToOneField(EOSSDialogueContext, on_delete=models.CASCADE)

    # Context that is used for those questions related with the engineer skill
    vassar_instrument = models.TextField(null=True)
    instrument_parameter = models.TextField(null=True)
    measurement_parameter = models.TextField(null=True)
    vassar_measurement = models.TextField(null=True)


class EngineerContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineerContext
        fields = '__all__'
