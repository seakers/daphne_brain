import json
from rest_framework.views import APIView
from rest_framework.response import Response

from daphne_brain.nlp_object import nlp
import dialogue.command_processing as command_processing
from auth_API.helpers import get_or_create_user_information
from daphne_context.models import Answer, AllowedCommand


class Command(APIView):
    """
    Process a command
    """
    daphne_version = ""
    command_options = []
    condition_names = []

    def post(self, request, format=None):
        # Preprocess the command
        processed_command = nlp(request.data['command'].strip().lower())

        # Classify the command, obtaining a command type
        command_types = command_processing.classify_command(processed_command, self.daphne_version)

        # Define context and see if it was already defined for this session
        user_info = get_or_create_user_information(request.session, request.user, self.daphne_version)

        # Remove all past answers related to this user
        Answer.objects.filter(user_information__exact=user_info).delete()
        AllowedCommand.objects.filter(user_information__exact=user_info).delete()

        if 'allowed_commands' in request.data:
            allowed_commands = json.loads(request.data['allowed_commands'])
            for command_type, command_list in allowed_commands.items():
                for command_number in command_list:
                    AllowedCommand.objects.create(user_information=user_info, command_type=command_type,
                                                  command_descriptor=command_number)

        # Act based on the types
        for command_type in command_types:
            command_class = self.command_options[command_type]
            condition_name = self.condition_names[command_type]

            answer = command_processing.command(processed_command, command_class,
                                                condition_name, user_info)
            Answer.objects.create(user_information=user_info,
                                  voice_answer=answer["voice_answer"],
                                  visual_answer_type=json.dumps(answer["visual_answer_type"]),
                                  visual_answer=json.dumps(answer["visual_answer"]))

        frontend_response = command_processing.think_response(user_info)

        return Response({'response': frontend_response})
