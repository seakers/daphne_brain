from rest_framework.views import APIView
from rest_framework.response import Response

from auth_API.helpers import get_or_create_user_information


class CheckConnection(APIView):

    def post(self, request, format=None):

        # --> 1. Get connection status and id
        user_info = get_or_create_user_information(request.session, request.user, 'EOSS')
        conn_status = user_info.mycroft_connection
        conn_id = user_info.mycroft_session
        print('--> CHECKING MYCROFT CONNECTIONS:', conn_id, conn_status)

        if conn_status is False:
            return Response({"connection": "false", "access_token": conn_id})
        else:
            return Response({"connection": "true"})



