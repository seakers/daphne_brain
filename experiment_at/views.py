import logging
import os
import json
import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from auth_API.helpers import get_or_create_user_information

# Get an instance of a logger
from daphne_context.models import UserInformation
from experiment_at.models import ATExperimentContext

logger = logging.getLogger('experiment')


def stage_type(id, stage_num):
    if id % 2 == 0:
        if stage_num == 0:
            return 'with_daphne'
        else:
            return 'without_daphne'
    else:
        if stage_num == 0:
            return 'without_daphne'
        else:
            return 'with_daphne'


# Create your views here.
class StartExperiment(APIView):

    def get(self, request, format=None):

        # Check for experiments folder
        results_dir = './experiment_at/results'
        #TODO create folders for each user if doesn't exist, otherwise...
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        # Obtain ID number
        new_id = len(os.listdir(results_dir)) #TODO save in user dir

        # Create File so ID does not get repeated
        open(os.path.join(results_dir, str(new_id) + '.json'), 'w')

        # Save experiment start info
        user_info = get_or_create_user_information(request.session, request.user, 'AT')

        # Ensure experiment is started again
        if hasattr(user_info, 'atexperimentcontext'):
            user_info.atexperimentcontext.delete()
        experiment_context = ATExperimentContext(user_information=user_info, is_running=False, experiment_id=-1,
                                                 current_state="")
        experiment_context.save()

        experiment_context.experiment_id = new_id

        # Specific to current experiment
        experiment_context.atexperimentstage_set.all().delete()
        experiment_context.atexperimentstage_set.create(type=stage_type(new_id, 0),
                                                        start_date=datetime.datetime.now(),
                                                        end_date=datetime.datetime.now(),
                                                        end_state="")
        experiment_context.atexperimentstage_set.create(type=stage_type(new_id, 1),
                                                        start_date=datetime.datetime.now(),
                                                        end_date=datetime.datetime.now(),
                                                        end_state="")

        # Save experiment started on database
        experiment_context.is_running = True

        experiment_context.save()

        # Prepare return for client
        experiment_stages = []
        for stage in experiment_context.atexperimentstage_set.all():
            experiment_stages.append(stage.type)

        return Response(experiment_stages)


class StartStage(APIView):

    def get(self, request, stage, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'AT')
        experiment_context = user_info.atexperimentcontext
        experiment_stage = experiment_context.atexperimentstage_set.all().order_by("id")[stage]
        experiment_stage.start_date = datetime.datetime.utcnow()
        experiment_stage.save()

        return Response({
            'start_date': experiment_stage.start_date.isoformat()
        })


class FinishStage(APIView):

    def get(self, request, stage, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'AT')
        experiment_context = user_info.atexperimentcontext
        experiment_stage = experiment_context.atexperimentstage_set.all().order_by("id")[stage]
        experiment_stage.end_date = datetime.datetime.utcnow()
        experiment_stage.end_state = experiment_context.current_state
        experiment_stage.save()

        return Response({
            'end_date': experiment_stage.end_date.isoformat()
        })


class ReloadExperiment(APIView):

    def get(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'AT')
        if hasattr(user_info, 'atexperimentcontext'):
            experiment_context = user_info.atexperimentcontext
            if experiment_context.is_running:
                return Response({'is_running': True, 'experiment_data': json.loads(experiment_context.current_state)})
        return Response({ 'is_running': False })
        
        
class FinishExperiment(APIView):

    def get(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'AT')
        experiment_context = user_info.atexperimentcontext

        # Save experiment results to file
        with open('./experiment_at/results/' + str(experiment_context.experiment_id) + '.json', 'w') as f:
            json_experiment = {
                "experiment_id": experiment_context.experiment_id,
                "current_state": json.loads(experiment_context.current_state),
                "stages": []
            }
            for stage in experiment_context.atexperimentstage_set.all():
                print(stage.type, stage.end_state)
                json_stage = {
                    "type": stage.type,
                    "start_date": stage.start_date.isoformat(),
                    "end_date": stage.end_date.isoformat(),
                    "end_state": json.loads(stage.end_state),
                    "actions": []
                }
                for action in stage.atexperimentaction_set.all():
                    json_action = {
                        "action": json.loads(action.action),
                        "date": action.date.isoformat()
                    }
                    json_stage["actions"].append(json_action)
                json_experiment["stages"].append(json_stage)
            json.dump(json_experiment, f)

        experiment_context.delete()

        return Response('Experiment finished correctly!')


class SubjectList(APIView):

    def get(self, request, format=None):
        subjects = UserInformation.objects.filter(atexperimentcontext__is_running__exact=True)
        subject_info = []
        for subject in subjects:
            if subject.user is not None:
                subject_info.append({
                    "name": subject.user.username,
                    "id": subject.id
                })
        return Response({
            "subjects": subject_info
        })

class GetState(APIView):

    def post(self, request, format=None):
        state_query = ATExperimentContext.objects.filter(user_information__id__exact=int(request.data["user_id"]))[0]
        state = json.loads(state_query.current_state)
        return Response(state)
