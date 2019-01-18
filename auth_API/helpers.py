from django.contrib.auth.models import User
from django.db import transaction

from daphne_API.models import UserInformation, EOSSContext, ActiveContext, EngineerContext, EDLContext
from merge_session.merge_db import MergeSession


def create_user_information(session_key=None, username=None, version='EOSS'):
    assert session_key is not None or username is not None

    with transaction.atomic():
        # Create the UserInformation with either session or username
        if username is not None and session_key is None:
            user_info = UserInformation(user=User.objects.get(username=username), daphne_version=version)
        elif session_key is not None and username is None:
            user_info = UserInformation(session=MergeSession.objects.get(session_key=session_key),
                                        daphne_version=version)
        else:
            raise Exception("Unexpected input for create_user_information")

        # Save the newly created user information in the database
        user_info.save()

        # Create the EOSS Context and its children
        eoss_context = EOSSContext(user_information=user_info, problem='', dataset_name='', last_arch_id=0,
                                   selected_arch_id=-1, added_archs_count=0, vassar_port=9090)
        eoss_context.save()

        active_context = ActiveContext(eosscontext=eoss_context, show_background_search_feedback=False,
                                       check_for_diversity=False, show_arch_suggestions=False)
        active_context.save()

        engineer_context = EngineerContext(eosscontext=eoss_context, vassar_instrument='', instrument_parameter='')
        engineer_context.save()

        edl_context = EDLContext(user_information=user_info, current_mat_file="", current_mat_file_for_print="",
                                  current_scorecard_file="", current_scorecard="")
        edl_context.save()

        return user_info


def get_user_information(session, user):

    if user.is_authenticated:
        # First try lookup by username
        userinfo_qs = UserInformation.objects.filter(user__exact=user)
    else:
        # Try to look by session key
        # If no session exists, create one here
        if session.session_key is None:
            session.create()
        session = MergeSession.objects.get(session_key=session.session_key)
        userinfo_qs = UserInformation.objects.filter(session__exact=session)

    if len(userinfo_qs) == 1:
        return userinfo_qs[0]
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