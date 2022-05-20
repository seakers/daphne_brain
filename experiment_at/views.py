import logging
import os
import json
import datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.views import APIView
from rest_framework.response import Response
from auth_API.helpers import get_or_create_user_information

# Get an instance of a logger
from daphne_context.models import UserInformation
from experiment_at.models import ATExperimentContext

logger = logging.getLogger('experiment')


def stage_type(id, stage_num):
    return 'with_daphne'


# Create your views here.
class StartExperiment(APIView):

    def get(self, request, format=None):

        # Check for experiments folder
        results_dir = './experiment_at/results'
        # TODO create folders for each user if doesn't exist, otherwise...
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        # Obtain ID number
        new_id = len(os.listdir(results_dir))  # TODO save in user dir

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
        # experiment_context.atexperimentstage_set.create(type=stage_type(new_id, 1),
        #                                                 start_date=datetime.datetime.now(),
        #                                                 end_date=datetime.datetime.now(),
        #                                                 end_state="")

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
                experiment_state = experiment_context.current_state
                if experiment_state == '':
                    experiment_data = json.loads('' or 'null')
                else:
                    experiment_data = json.loads(experiment_state)
                return Response({'is_running': True, 'experiment_data': experiment_data})
        return Response({'is_running': False})


class SituationalAwareness(APIView):

    def post(self, request, format=None):
        # Retrieve the user from the user id
        state_query = UserInformation.objects.filter(id__exact=int(request.data["user_id"]))

        # If found
        if len(state_query) > 0:
            # Retrieve the channel name and channel layer
            channel_name = state_query[0].channel_name
            channel_layer = get_channel_layer()

            # Build and send a command to the frontend
            command = {'type': 'situational_awareness',
                       'content': ''}
            async_to_sync(channel_layer.send)(channel_name, command)

        return Response()


class Workload(APIView):

    def post(self, request, format=None):
        # Retrieve the user from the user id
        state_query = UserInformation.objects.filter(id__exact=int(request.data["user_id"]))

        # If found
        if len(state_query) > 0:
            # Retrieve the channel name and channel layer
            channel_name = state_query[0].channel_name
            channel_layer = get_channel_layer()

            # Build and send a command to the frontend
            command = {'type': 'workload',
                       'workload_problem': request.data['workload_problem']}
            async_to_sync(channel_layer.send)(channel_name, command)

        return Response()


class Confidence(APIView):

    def post(self, request, format=None):
        # Retrieve the user from the user id
        state_query = UserInformation.objects.filter(id__exact=int(request.data["user_id"]))

        # If found
        if len(state_query) > 0:
            # Retrieve the channel name and channel layer
            channel_name = state_query[0].channel_name
            channel_layer = get_channel_layer()

            # Build and send a command to the frontend
            command = {'type': 'confidence'}
            async_to_sync(channel_layer.send)(channel_name, command)

        return Response()


class SendMsgCorrect(APIView):

    def post(self, request, format=None):
        # Retrieve the user from the user id
        state_query = UserInformation.objects.filter(id__exact=int(request.data["user_id"]))

        # If found
        if len(state_query) > 0:
            # Retrieve the channel name and channel layer
            channel_name = state_query[0].channel_name
            channel_layer = get_channel_layer()

            # Build and send a command to the frontend
            command = {'type': 'send_msg_correct'}
            async_to_sync(channel_layer.send)(channel_name, command)

        return Response()


class SendMsgIncorrect(APIView):

    def post(self, request, format=None):
        # Retrieve the user from the user id
        state_query = UserInformation.objects.filter(id__exact=int(request.data["user_id"]))

        # If found
        if len(state_query) > 0:
            # Retrieve the channel name and channel layer
            channel_name = state_query[0].channel_name
            channel_layer = get_channel_layer()

            # Build and send a command to the frontend
            command = {'type': 'send_msg_incorrect'}
            async_to_sync(channel_layer.send)(channel_name, command)

        return Response()


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
                end_state = stage.end_state
                if end_state == '':
                    json_end_state = json.loads('' or 'null')
                else:
                    json_end_state = json.loads(end_state)
                json_stage = {
                    "type": stage.type,
                    "start_date": stage.start_date.isoformat(),
                    "end_date": stage.end_date.isoformat(),
                    "end_state": json_end_state,
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
        state_query = ATExperimentContext.objects.filter(user_information__id__exact=int(request.data["user_id"]))
        if len(state_query) > 0:
            current_state = state_query[0].current_state
            if current_state != '':
                json_current_state = json.loads(current_state)
            else:
                json_current_state = json.loads('' or 'null')
            state = json_current_state
            return Response(state)
        else:
            return Response('None')


class FinishExperimentFromMcc(APIView):

    def post(self, request, format=None):
        # Retrieve the user from the user id
        state_query = UserInformation.objects.filter(id__exact=int(request.data["user_id"]))

        # If found
        if len(state_query) > 0:
            # Retrieve the channel name and channel layer
            channel_name = state_query[0].channel_name
            channel_layer = get_channel_layer()

            # Build and send a command to the frontend
            command = {'type': 'finish_experiment_from_mcc',
                       'content': ''}
            async_to_sync(channel_layer.send)(channel_name, command)

        return Response()


class ForceFinishExperimentFromMcc(APIView):

    def post(self, request, format=None):
        # Retrieve the user from the user id
        user_information_query = UserInformation.objects.filter(id__exact=int(request.data["user_id"]))

        # If found
        if len(user_information_query) > 0:
            # Finish stage
            user_information = user_information_query[0]
            experiment_context = user_information.atexperimentcontext
            experiment_stage = experiment_context.atexperimentstage_set.all().order_by("id")[0]
            experiment_stage.end_date = datetime.datetime.utcnow()
            experiment_stage.end_state = experiment_context.current_state
            experiment_stage.save()

            # Finish experiment
            # Save experiment results to file
            with open('./experiment_at/results/' + str(experiment_context.experiment_id) + '.json', 'w') as f:
                print(experiment_context.current_state)
                json_experiment = {
                    "experiment_id": experiment_context.experiment_id,
                    "current_state": experiment_context.current_state if not '' else '',
                    "stages": []
                }
                for stage in experiment_context.atexperimentstage_set.all():
                    print(stage.type, stage.end_state)
                    end_state = stage.end_state
                    if end_state == '':
                        json_end_state = json.loads('' or 'null')
                    else:
                        json_end_state = json.loads(end_state)
                    json_stage = {
                        "type": stage.type,
                        "start_date": stage.start_date.isoformat(),
                        "end_date": stage.end_date.isoformat(),
                        "end_state": json_end_state,
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


class TurnOffAlarms(APIView):
    def post(self, request, format=None):
        # Retrieve user from the user id
        state_query = UserInformation.objects.filter(id__exact=int(request.data["user_id"]))

        # If found
        if len(state_query) > 0:
            # Retrieve the channel name and layer
            channel_name = state_query[0].channel_name
            channel_layer = get_channel_layer()

            # Build command to send to frontend
            command = {'type': 'turn_off_alarms'}
            async_to_sync(channel_layer.send)(channel_name, command)

        return Response()
