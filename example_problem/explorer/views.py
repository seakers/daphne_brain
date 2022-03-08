from rest_framework.views import APIView
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from auth_API.helpers import get_or_create_user_information


class StartGA(APIView):
    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                # TODO: Start GA with correct settings

                return Response({
                    "status": 'GA started correctly!'
                })

            except Exception as exc:
                return Response({
                    "error": "Error starting the GA",
                    "exception": str(exc)
                })

        else:
            return Response({
                "error": "This is only available to registered users!"
            })


class StopGA(APIView):
    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                # TODO: Stop GA with correct settings

                return Response({
                    "status": 'GA stopped correctly!'
                })

            except Exception as exc:
                return Response({
                    "error": "Error stopping the GA",
                    "exception": str(exc)
                })

        else:
            return Response({
                "error": "This is only available to registered users!"
            })


class CheckGA(APIView):
    def post(self, request, format=None):
        if request.user.is_authenticated:
            try:
                # TODO: Check status of GA

                return Response({
                    'ga_status': "TODO"
                })

            except Exception as exc:
                return Response({
                    "error": "Error checking the GA status",
                    "exception": str(exc)
                })

        else:
            return Response({
                "error": "This is only available to registered users!"
            })
