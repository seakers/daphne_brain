from django.contrib.auth.models import User
from django.db import transaction
from EOSS.aws.utils import get_boto3_client
import random
import string
from EDL.models import EDLContext
from EOSS.models import EOSSContext, ActiveContext
from experiment.models import ExperimentContext
from daphne_context.models import UserInformation
from django.contrib.sessions.models import Session

def new_eval_request_queue():
    print('--> GENERATING USER EVAL REQUEST QUEUE')
    sqs_client = get_boto3_client('sqs')
    queue_name = 'eval-request-queue-' + str(''.join(random.choices(string.ascii_uppercase + string.digits, k=15)))
    list_response = sqs_client.list_queues()
    if 'QueueUrls' in list_response:
        queue_names = [url.split("/")[-1] for url in list_response['QueueUrls']]
        if queue_name in queue_names:
            queue_url_idx = queue_names.index(queue_name)
            queue_url = list_response['QueueUrls'][queue_url_idx]
            sqs_client.purge_queue(QueueUrl=queue_url)
            return queue_url
        else:
            return sqs_client.create_queue(QueueName=queue_name)['QueueUrl']
    else:
        return sqs_client.create_queue(QueueName=queue_name)['QueueUrl']

def new_eval_response_queue():
    print('--> GENERATING USER EVAL RESPONSE QUEUE')
    sqs_client = get_boto3_client('sqs')
    queue_name = 'eval-response-queue-' + str(''.join(random.choices(string.ascii_uppercase + string.digits, k=15)))
    list_response = sqs_client.list_queues()
    if 'QueueUrls' in list_response:
        queue_names = [url.split("/")[-1] for url in list_response['QueueUrls']]
        if queue_name in queue_names:
            queue_url_idx = queue_names.index(queue_name)
            queue_url = list_response['QueueUrls'][queue_url_idx]
            sqs_client.purge_queue(QueueUrl=queue_url)
            return queue_url
        else:
            return sqs_client.create_queue(QueueName=queue_name)['QueueUrl']
    else:
        return sqs_client.create_queue(QueueName=queue_name)['QueueUrl']


def create_queue_if_dne(queue_url):
    sqs_client = get_boto3_client('sqs')

    # --> 1. Check to see if queue exists
    list_response = sqs_client.list_queues()
    if 'QueueUrls' in list_response:
        if queue_url in list_response['QueueUrls']:
            return True

    # --> 2. Queue dne, create it
    queue_name = queue_url.split("/")[-1]
    sqs_client.create_queue(QueueName=queue_name)
    return True


def create_user_information(session_key=None, username=None, version='EOSS'):
    assert session_key is not None or username is not None

    with transaction.atomic():
        # Create the UserInformation with either session or username
        if username is not None and session_key is None:
            user_info = UserInformation(user=User.objects.get(username=username), daphne_version=version)
        elif session_key is not None and username is None:
            user_info = UserInformation(session=Session.objects.get(session_key=session_key),
                                        daphne_version=version)
        else:
            raise Exception("Unexpected input for create_user_information")

        # Save the newly created user information in the database
        user_info.eval_request_queue = new_eval_request_queue()
        user_info.eval_response_queue = new_eval_response_queue()
        user_info.save()

        # Create the EOSS Context and its children
        eoss_context = EOSSContext(user_information=user_info, dataset_id=-1, last_arch_id=0, selected_arch_id=-1, 
                                   added_archs_count=0, group_id=1, problem_id=1)
        eoss_context.save()

        active_context = ActiveContext(eosscontext=eoss_context, show_background_search_feedback=False,
                                       check_for_diversity=False, show_arch_suggestions=False)
        active_context.save()

        experiment_context = ExperimentContext(user_information=user_info, is_running=False, experiment_id=-1,
                                               current_state="")
        experiment_context.save()

        edl_context = EDLContext(user_information=user_info, current_mat_file="", current_mat_file_for_print="",
                                 current_scorecard_file="", current_scorecard="")
        edl_context.save()

        return user_info


def get_user_information(session, user):

    if user.is_authenticated:
        # First try lookup by username
        userinfo_qs = UserInformation.objects.filter(user__exact=user).select_related("user", "eosscontext", "eosscontext__activecontext", "experimentcontext", "edlcontext")
    else:
        # Try to look by session key
        # If no session exists, create one here
        if session.session_key is None:
            session.create()
        session = Session.objects.get(session_key=session.session_key)
        userinfo_qs = UserInformation.objects.filter(session_id__exact=session.session_key).select_related("user", "eosscontext", "eosscontext__activecontext", "experimentcontext", "edlcontext")

    if len(userinfo_qs) >= 1:
        user_info = userinfo_qs[0]
        create_queue_if_dne(user_info.eval_request_queue)
        create_queue_if_dne(user_info.eval_response_queue)
        return user_info
    elif len(userinfo_qs) == 0:
        raise Exception("Information not already created!")


def get_or_create_user_information(session, user, version='EOSS'):
    try:
        userinfo = get_user_information(session, user)
        return userinfo
    except Exception:
        if user.is_authenticated:
            return create_user_information(username=user.username, version=version)
        else:
            return create_user_information(session_key=session.session_key, version=version)
