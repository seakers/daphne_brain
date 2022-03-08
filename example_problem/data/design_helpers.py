from example_problem.explorer.diversifier import activate_diversifier
from example_problem.models import Design
import json
from threading import Lock

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
        examplecontext = get_user_information(session, user).examplecontext
        design["id"] = examplecontext.last_arch_id
        if active:
            Design.objects.create(activecontext=examplecontext.activecontext,
                                  id=examplecontext.last_arch_id,
                                  inputs=json.dumps(design['inputs']),
                                  outputs=json.dumps(design['outputs']))
        else:
            Design.objects.create(examplecontext=examplecontext,
                                  id=examplecontext.last_arch_id,
                                  inputs=json.dumps(design['inputs']),
                                  outputs=json.dumps(design['outputs']))
            examplecontext.added_archs_count += 1

        examplecontext.last_arch_id += 1

        if examplecontext.added_archs_count >= 5:
            examplecontext.added_archs_count = 0
            activate_diversifier(examplecontext)

        examplecontext.save()
    return design
