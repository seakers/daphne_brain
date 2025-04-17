import logging

from channels.layers import get_channel_layer
from rest_framework.views import APIView
from rest_framework.response import Response

from EOSS.explorer.helpers import send_archs_from_queue_to_main_dataset, send_archs_back
from auth_API.helpers import get_or_create_user_information


# Get an instance of a logger
logger = logging.getLogger('EOSS.settings')


class ChangePort(APIView):
    def post(self, request, format=None):
        new_port = request.data['port']
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        user_info.eosscontext.vassar_port = new_port
        user_info.eosscontext.save()
        user_info.save()
        return Response({
            "status": "Port changed correctly"
        })


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
                'show_background_search_feedback': user_info.eosscontext.activecontext.show_background_search_feedback,
                'check_for_diversity': user_info.eosscontext.activecontext.check_for_diversity,
                'show_arch_suggestions': user_info.eosscontext.activecontext.show_arch_suggestions,
            })
        else:
            return Response({
                'error': 'User not logged in!'
            })

    def post(self, request, format=None):
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        if 'show_background_search_feedback' in request.data:
            show_background_search_feedback = request.data['show_background_search_feedback'] == 'true'
            user_info.eosscontext.activecontext.show_background_search_feedback = show_background_search_feedback
            if show_background_search_feedback:
                back_list = send_archs_from_queue_to_main_dataset(user_info)
                channel_layer = get_channel_layer()
                send_archs_back(channel_layer, user_info.channel_name, back_list)
        if 'check_for_diversity' in request.data:
            check_for_diversity = request.data['check_for_diversity'] == 'true'
            user_info.eosscontext.activecontext.check_for_diversity = check_for_diversity
        if 'show_arch_suggestions' in request.data:
            show_arch_suggestions = request.data['show_arch_suggestions'] == 'true'
            user_info.eosscontext.activecontext.show_arch_suggestions = show_arch_suggestions

        user_info.eosscontext.activecontext.save()
        user_info.save()
        return Response({
            "status": "Settings have been updated"
        })
