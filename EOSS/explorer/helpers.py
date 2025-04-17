import datetime
import json

from asgiref.sync import async_to_sync

from EOSS.models import Design
from EOSS.explorer.diversifier import activate_diversifier
from daphne_context.models import DialogueHistory


def send_archs_back(channel_layer, channel_name, archs):
    async_to_sync(channel_layer.send)(channel_name,
                                      {
                                          'type': 'ga.new_archs',
                                          'archs': archs
                                      })


def send_archs_from_queue_to_main_dataset(context):
    background_queue_qs = Design.objects.filter(activecontext_id__exact=context.eosscontext.activecontext.id).order_by('id')
    arch_list = []
    for design in background_queue_qs.all():
        design.activecontext = None
        design.eosscontext = context.eosscontext
        design.save()
        context.eosscontext.added_archs_count += 1
        context.eosscontext.save()
        arch_list.append({
            'id': design.id,
            'inputs': json.loads(design.inputs),
            'outputs': json.loads(design.outputs),
        })

    if context.eosscontext.added_archs_count >= 5:
        context.eosscontext.added_archs_count = 0
        context.eosscontext.save()
        activate_diversifier(context.eosscontext)

    return arch_list


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
                                   writer="daphne",
                                   date=datetime.datetime.utcnow())
    return message
