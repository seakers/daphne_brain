import json

from asgiref.sync import async_to_sync

from daphne_API.diversifier import activate_diversifier
from daphne_API.models import Design


def send_archs_back(channel_layer, channel_name, archs):
    async_to_sync(channel_layer.send)(channel_name,
                                      {
                                          'type': 'ga.new_archs',
                                          'archs': archs
                                      })


def send_archs_from_queue_to_main_dataset(context):
    background_queue_qs = Design.objects.filter(activecontext_id__exact=context.eosscontext.activecontext.id)
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