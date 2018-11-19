import json

from asgiref.sync import async_to_sync

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
        arch_list.append({
            'id': design.id,
            'inputs': json.loads(design.inputs),
            'outputs': json.loads(design.outputs),
        })
    return arch_list