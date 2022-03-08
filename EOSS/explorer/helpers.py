import datetime
import json

from asgiref.sync import async_to_sync

from EOSS.explorer.diversifier import activate_diversifier
from daphne_context.models import DialogueHistory


def generate_background_search_message(user_info):
    message = {
        'voice_message': 'The background search has found several architectures, but you have chosen to not show '
                         'them. Do you want to see them now?',
        'visual_message_type': ['active_message'],
        'visual_message': [
            {
                'message': 'The background search has found several architectures, but you have chosen to not show '
                           'them. Do you want to see them now?',
                'setting': 'show_background_search_feedback'
            }
        ],
        "writer": "daphne",
    }
    DialogueHistory.objects.create(user_information=user_info,
                                   voice_message=message["voice_message"],
                                   visual_message_type=json.dumps(message["visual_message_type"]),
                                   visual_message=json.dumps(message["visual_message"]),
                                   dwriter="daphne",
                                   date=datetime.datetime.utcnow())
    return message
