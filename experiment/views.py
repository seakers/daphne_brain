import logging
import os
import json
import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from auth_API.helpers import get_or_create_user_information, get_user_information

# Get an instance of a logger
from experiment.models import ExperimentContext

logger = logging.getLogger('experiment')


def stage_type(id, stage_num):
    stage_config = id % 2 
    if stage_config == 0:
        if stage_num == 0:
            return 'daphne_baseline'
        else:
            return 'daphne_group'
    elif stage_config == 1:
        if stage_num == 0:
            return 'daphne_group'
        else:
            return 'daphne_baseline'


# Create your views here.
class StartExperiment(APIView):

    def get(self, request, format=None):

        # Check for experiments folder
        results_dir = './experiment/results'
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        # Obtain ID number
        new_id = len(os.listdir(results_dir))

        # Create File so ID does not get repeated
        file_path = os.path.join(results_dir, str(new_id) + '.json')
        if os.path.exists(file_path):
            file_path = os.path.join(results_dir, str(new_id) + '_1.json')
        open(file_path, 'w')

        # Save experiment start info
        
        # User info needs to already exist and have user marked as experiment user
        user_info = get_user_information(request.session, request.user)

        if not user_info.is_experiment_user:
            return Response({
                "error": "User is not set up as experiment user"
            })

        # Ensure experiment is started again
        if hasattr(user_info, 'experimentcontext'):
            user_info.experimentcontext.delete()
        experiment_context = ExperimentContext(user_information=user_info, is_running=False, experiment_id=-1,
                                               current_state="")
        experiment_context.save()

        experiment_context.experiment_id = new_id

        # Specific to current experiment
        experiment_context.experimentstage_set.all().delete()

        experiment_context.experimentstage_set.create(type=stage_type(new_id, 0),
                                                      start_date=datetime.datetime.now(),
                                                      end_date=datetime.datetime.now(),
                                                      end_state="")
        experiment_context.experimentstage_set.create(type=stage_type(new_id, 1),
                                                      start_date=datetime.datetime.now(),
                                                      end_date=datetime.datetime.now(),
                                                      end_state="")

        # Save experiment started on database
        experiment_context.is_running = True

        experiment_context.save()

        # Prepare return for client
        experiment_stages = []
        for stage in experiment_context.experimentstage_set.all():
            experiment_stages.append(stage.type)

        return Response(experiment_stages)


class StartStage(APIView):

    def get(self, request, stage, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        experiment_context = user_info.experimentcontext
        experiment_stage = experiment_context.experimentstage_set.all().order_by("id")[stage]
        experiment_stage.start_date = datetime.datetime.utcnow()
        experiment_stage.save()

        return Response({
            'start_date': experiment_stage.start_date.isoformat()
        })


class FinishStage(APIView):

    def get(self, request, stage, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        experiment_context = user_info.experimentcontext
        experiment_stage = experiment_context.experimentstage_set.all().order_by("id")[stage]
        experiment_stage.end_date = datetime.datetime.utcnow()
        experiment_stage.end_state = experiment_context.current_state
        experiment_stage.save()

        return Response({
            'end_date': experiment_stage.end_date.isoformat()
        })


class ReloadExperiment(APIView):

    def get(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        if hasattr(user_info, 'experimentcontext'):
            experiment_context = user_info.experimentcontext
            if experiment_context.is_running:
                return Response({'is_running': True, 'experiment_data': json.loads(experiment_context.current_state)})
        return Response({ 'is_running': False })
        
        
class FinishExperiment(APIView):

    def get(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        experiment_context = user_info.experimentcontext

        # Save experiment results to file
        save_experiment_to_file(experiment_context)

        experiment_context.delete()

        return Response('Experiment finished correctly!')


def save_experiment_to_file(experiment_context: ExperimentContext):
    # Save experiment results to file
    with open('./experiment/results/' + str(experiment_context.experiment_id) + '.json', 'w') as f:
        json_experiment = {
            "experiment_id": experiment_context.experiment_id,
            "current_state": json.loads(experiment_context.current_state) if experiment_context.current_state != "" else "",
            "stages": []
        }
        for stage in experiment_context.experimentstage_set.all():
            json_stage = {
                "type": stage.type,
                "start_date": stage.start_date.isoformat(),
                "end_date": stage.end_date.isoformat(),
                "end_state": json.loads(stage.end_state) if stage.end_state != "" else "",
                "actions": []
            }
            for action in stage.experimentaction_set.all():
                json_action = {
                    "action": json.loads(action.action) if action.action != "" else "",
                    "date": action.date.isoformat()
                }
                json_stage["actions"].append(json_action)
            json_experiment["stages"].append(json_stage)
        json.dump(json_experiment, f)
