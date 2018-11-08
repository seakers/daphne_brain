from django.contrib.auth.models import User
from django.db import transaction

from daphne_API.models import UserInformation, EOSSContext, ActiveContext, EngineerContext
from merge_session.merge_db import MergeSession


def create_user_information(session_key=None, username=None, version='EOSS'):
    assert session_key is not None or username is not None

    with transaction.atomic():
        # Create the EOSS Context and its children
        active_context = ActiveContext(show_background_search_feedback=False, check_for_diversity=False,
                                       show_arch_suggestions=False)
        active_context.save()

        engineer_context = EngineerContext(vassar_instrument='', instrument_parameter='')
        engineer_context.save()

        eoss_context = EOSSContext(problem='', dataset_name='', last_arch_id=0, selected_arch_id=-1, vassar_port=9090,
                                   active_context=active_context, engineer_context=engineer_context)
        eoss_context.save()

        # Create the UserInformation with either session or username
        if username is not None and session_key is None:
            user_info = UserInformation(user=User.objects.get(username=username), daphne_version=version,
                                        eoss_context=eoss_context)
        elif session_key is not None and username is None:
            user_info = UserInformation(session=MergeSession.objects.get(session_key=session_key), daphne_version=version,
                                        eoss_context=eoss_context)
        else:
            raise Exception("Unexpected input for create_user_information")

        # Save the newly created user information in the database
        user_info.save()

        return user_info

def get_or_create_user_information(request, version):

    if request.user.is_authenticated:
        # First try lookup by username
        session_qs = UserInformation.objects.filter(user__exact=request.user)
    else:
        # Try to look by session key
        session_qs = UserInformation.objects.filter(session__exact=MergeSession.objects.get(session_key=request.session.session_key))

    if len(session_qs) == 1:
        return session_qs[0]
    elif len(session_qs) == 0:
        if request.user.is_authenticated:
            return create_user_information(username=request.user.username, version=version)
        else:
            return create_user_information(session_key=request.session.session_key, version=version)
