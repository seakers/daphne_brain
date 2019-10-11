from rest_framework.views import APIView
from rest_framework.response import Response
import threading
import time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from auth_API.helpers import get_or_create_user_information


class SimulateTelemetry(APIView):
    def post(self, request):

        def read_and_update():
            thread_user_info = get_or_create_user_information(request.session, request.user, 'AT')
            channel_layer = get_channel_layer()
            k = 1
            while k < 6:
                time.sleep(1)
                command = {}
                command['type'] = 'console_text'
                command['text'] = 'Second: ' + str(k)
                async_to_sync(channel_layer.send)(thread_user_info.channel_name, command)
                k += 1
            return None

        thread = threading.Thread(target=read_and_update)
        thread.start()
        return Response()
