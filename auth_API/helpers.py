import asyncio

from django.contrib.auth.models import User
from django.db import transaction

from EDL.models import EDLContext
import threading
from EOSS.models import EOSSContext, ActiveContext
from AT.models import ATContext, ActiveATContext
from experiment.models import ExperimentContext
from daphne_context.models import UserInformation
from django.contrib.sessions.models import Session
from EOSS.aws.service.ServiceManager import ServiceManager

from asgiref.sync import async_to_sync

from mycroft.utils import generate_unique_mycroft_session


""" Sequence: get_or_create_user_information

    1. Check if user is authenticated (logged in / out)
     - if logged in: 
        - get user_info by: UserInformation.objects.filter(user__exact=user)
     - if not logged in: 
        - get or create session object
        - get user_info by: UserInformation.objects.filter(session_id__exact=session.session_key)

    2. Create UserInformation (user must be logged in, )



"""

def get_session(session_key):
    session_objs = Session.objects.filter(session_key=session_key)
    if len(session_objs) == 0:
        return None
    else:
        return session_objs[0]



def get_or_create_user_information(session, user, version='EOSS'):
    # print('--> get_or_create_user_information:', session, user)
    userinfo = get_user_information(session, user)
    if userinfo is not None:
        return userinfo
    if user.is_authenticated:
        return create_user_information(username=user.username, version=version)
    else:
        return create_user_information(session_key=session.session_key, version=version)


def get_user_information(session, user):

    if user.is_authenticated:
        # First try lookup by username
        userinfo_qs = UserInformation.objects.filter(user__exact=user).select_related("user", "eosscontext", "eosscontext__activecontext", "experimentcontext", "edlcontext")
    else:
        # Try to look by session key
        # If no session exists, create one here
        if session.session_key is None:
            print('--> GENERATING SESSION: get_user_information')
            session.create()

        q_session = get_session(session.session_key)
        if q_session is None:
            return None
        else:
            userinfo_qs = UserInformation.objects.filter(session_id__exact=q_session.session_key).select_related("user",
                                                                                                               "eosscontext",
                                                                                                               "eosscontext__activecontext",
                                                                                                               "experimentcontext",
                                                                                                               "edlcontext")
    if len(userinfo_qs) >= 1:
        user_info = userinfo_qs[0]
        return user_info
    elif len(userinfo_qs) == 0:
        return None



def create_user_information(session_key=None, username=None, version='EOSS'):
    assert session_key is not None or username is not None

    with transaction.atomic():

        # --> 1. UserInformation
        if username is not None and session_key is None:
            user_info = UserInformation(user=User.objects.get(username=username), daphne_version=version)
        elif session_key is not None and username is None:
            q_session = get_session(session_key)
            if q_session is None:
                return None
            user_info = UserInformation(session=q_session, daphne_version=version)
        else:
            raise Exception("Unexpected input for create_user_information")


        # --> Mycroft fields
        user_info.mycroft_session = generate_unique_mycroft_session()
        user_info.save()



        # --> 2. EOSSContext
        eoss_context = EOSSContext(user_information=user_info, dataset_id=-1, last_arch_id=0, selected_arch_id=-1,
                                   added_archs_count=0, group_id=1, problem_id=1)
        eoss_context.save()


        # --> ActiveContext
        active_context = ActiveContext(eosscontext=eoss_context, check_for_diversity=False, show_engineer_suggestions=False,
                                       engineer_suggestions_frequency=3, show_historian_suggestions=False,
                                       historian_suggestions_frequency=3, show_analyst_suggestions=False,
                                       analyst_suggestions_frequency=45)
        active_context.save()



        # --> ExperimentContext
        experiment_context = ExperimentContext(user_information=user_info, is_running=False, experiment_id=-1,
                                               current_state="")
        experiment_context.save()


        # --> EDLContext
        edl_context = EDLContext(user_information=user_info, current_mat_file="", current_mat_file_for_print="",
                                 current_scorecard_file="", current_scorecard_path="", selected_case=-1,
                                 current_mission="", current_metrics_of_interest="")
        edl_context.save()

        # --> ATContext
        at_context = ATContext(user_information=user_info)
        at_context.save()
        

        return user_info
