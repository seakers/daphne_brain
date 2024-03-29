import json
import threading
from threading import Lock

from EOSS.explorer.diversifier import activate_diversifier
from EOSS.models import EOSSContext
from auth_API.helpers import get_user_information
from daphne_context.models import UserInformation

design_lock = Lock()


def add_design(session, user):
    """
    This function adds a design to the database, updates all related counters and calls related functions if needed.
    Always use this function to add new designs
    :param user_info: The user_info object from the DB, use this or active
    :param design: A JSON dictionary with the design, with fields id, inputs and outputs
    :return: Nothing
    """

    with design_lock:
        user_info = get_user_information(session, user)
        eosscontext = user_info.eosscontext
        print("--> last_arch_id:", eosscontext.last_arch_id)
        eosscontext.added_archs_count += 1

        eosscontext.last_arch_id += 1

        if eosscontext.added_archs_count >= 5:
            eosscontext.added_archs_count = 0
            activate_diversifier(user_info)

        eosscontext.save()

