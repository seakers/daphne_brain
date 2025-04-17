import json
import threading
from threading import Lock

from EOSS.explorer.diversifier import activate_diversifier
from EOSS.models import EOSSContext, Design
from auth_API.helpers import get_user_information
from daphne_context.models import UserInformation

design_lock = Lock()


def add_design(design, session, user, active: bool):
    """
    This function adds a design to the database, updates all related counters and calls related functions if needed.
    Always use this function to add new designs
    :param user_info: The user_info object from the DB, use this or active
    :param design: A JSON dictionary with the design, with fields id, inputs and outputs
    :return: Nothing
    """

    with design_lock:
        eosscontext = get_user_information(session, user).eosscontext
        design["id"] = eosscontext.last_arch_id
        if active:
            Design.objects.create(activecontext=eosscontext.activecontext,
                                  id=eosscontext.last_arch_id,
                                  inputs=json.dumps(design['inputs']),
                                  outputs=json.dumps(design['outputs']))
        else:
            Design.objects.create(eosscontext=eosscontext,
                                  id=eosscontext.last_arch_id,
                                  inputs=json.dumps(design['inputs']),
                                  outputs=json.dumps(design['outputs']))
            eosscontext.added_archs_count += 1

        eosscontext.last_arch_id += 1

        if eosscontext.added_archs_count >= 5:
            eosscontext.added_archs_count = 0
            activate_diversifier(eosscontext)

        eosscontext.save()
    return design
