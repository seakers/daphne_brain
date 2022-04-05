import logging

from channels.layers import get_channel_layer
from rest_framework.views import APIView
from rest_framework.response import Response

from auth_API.helpers import get_or_create_user_information


# Get an instance of a logger
logger = logging.getLogger('EOSS.settings')


class ClearSession(APIView):
    """ Clears the Daphne Session.
    """
    def post(self, request, format=None):
        from EOSS.settings.daphne_fields import daphne_fields

        # Remove all fields from session if they exist
        for field in daphne_fields:
            if field in request.session:
                del request.session[field]

        return Response({
            "status": "Session has been correctly cleaned"
        })


class ActiveFeedbackSettings(APIView):
    """ Returns the values for the different active daphne settings
    """
    def get(self, request, format=None):
        if request.user.is_authenticated:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

            return Response({
                'check_for_diversity': user_info.eosscontext.activecontext.check_for_diversity,
                'show_engineer_suggestions': user_info.eosscontext.activecontext.show_engineer_suggestions,
                'engineer_suggestions_frequency': user_info.eosscontext.activecontext.engineer_suggestions_frequency,
                'show_historian_suggestions': user_info.eosscontext.activecontext.show_historian_suggestions,
                'historian_suggestions_frequency': user_info.eosscontext.activecontext.historian_suggestions_frequency,
                'show_analyst_suggestions': user_info.eosscontext.activecontext.show_analyst_suggestions,
                'analyst_suggestions_frequency': user_info.eosscontext.activecontext.analyst_suggestions_frequency,
            })
        else:
            return Response({
                'error': 'User not logged in!'
            })

    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        if 'check_for_diversity' in request.data:
            check_for_diversity = request.data['check_for_diversity'] == 'true'
            user_info.eosscontext.activecontext.check_for_diversity = check_for_diversity

        if 'show_engineer_suggestions' in request.data:
            show_engineer_suggestions = request.data['show_engineer_suggestions'] == 'true'
            user_info.eosscontext.activecontext.show_engineer_suggestions = show_engineer_suggestions
        if 'engineer_suggestions_frequency' in request.data:
            engineer_suggestions_frequency = int(request.data['engineer_suggestions_frequency'])
            user_info.eosscontext.activecontext.engineer_suggestions_frequency = engineer_suggestions_frequency

        if 'show_historian_suggestions' in request.data:
            show_historian_suggestions = request.data['show_historian_suggestions'] == 'true'
            user_info.eosscontext.activecontext.show_historian_suggestions = show_historian_suggestions
        if 'historian_suggestions_frequency' in request.data:
            historian_suggestions_frequency = int(request.data['historian_suggestions_frequency'])
            user_info.eosscontext.activecontext.historian_suggestions_frequency = historian_suggestions_frequency

        if 'show_analyst_suggestions' in request.data:
            show_analyst_suggestions = request.data['show_analyst_suggestions'] == 'true'
            user_info.eosscontext.activecontext.show_analyst_suggestions = show_analyst_suggestions
        if 'analyst_suggestions_frequency' in request.data:
            analyst_suggestions_frequency = int(request.data['analyst_suggestions_frequency'])
            user_info.eosscontext.activecontext.analyst_suggestions_frequency = analyst_suggestions_frequency

        user_info.eosscontext.activecontext.save()
        user_info.save()
        return Response({
            "status": "Settings have been updated"
        })

class ExpertiseSettings(APIView):
    """ Returns the values for the different active daphne settings
    """
    def get(self, request, format=None):
        if request.user.is_authenticated:
            user_info = get_or_create_user_information(request.session, request.user, 'EOSS')

            return Response({
                'is_domain_expert': user_info.is_domain_expert
            })
        else:
            return Response({
                'error': 'User not logged in!'
            })

    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        if 'is_domain_expert' in request.data:
            is_domain_expert = request.data['is_domain_expert'] == 'true'
            user_info.is_domain_expert = is_domain_expert
        user_info.save()
        return Response({
            "status": "Settings have been updated"
        })