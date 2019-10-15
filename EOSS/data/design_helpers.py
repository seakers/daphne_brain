import json

from EOSS.explorer.diversifier import activate_diversifier
from EOSS.models import EOSSContext, Design


def add_design(design, eosscontext: EOSSContext, active: bool):
    """
    This function adds a design to the database, updates all related counters and calls related functions if needed.
    Always use this function to add new designs
    :param eosscontext: The eosscontext object from the DB, use this or active
    :param activecontext: The activecontext object from the DB, use this or eoss
    :param design: A JSON dictionary with the design, with fields id, inputs and outputs
    :return: Nothing
    """

    if active:
        Design.objects.create(activecontext=eosscontext.activecontext,
                              id=design['id'],
                              inputs=json.dumps(design['inputs']),
                              outputs=json.dumps(design['outputs']))
    else:
        Design.objects.create(eosscontext=eosscontext,
                              id=design['id'],
                              inputs=json.dumps(design['inputs']),
                              outputs=json.dumps(design['outputs']))
        eosscontext.added_archs_count += 1

    eosscontext.last_arch_id += 1

    if eosscontext.added_archs_count >= 5:
        eosscontext.added_archs_count = 0
        activate_diversifier(eosscontext)

    eosscontext.save()
