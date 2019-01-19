from django.conf import settings

if 'EOSS' in settings.ACTIVE_MODULES:
    import daphne_API.eoss.runnable_functions as eoss
    import daphne_API.eoss.runnable_functions.analyst
    import daphne_API.eoss.runnable_functions.critic
    import daphne_API.eoss.runnable_functions.engineer

if 'EDL' in settings.ACTIVE_MODULES:
    import daphne_API.edl.runnable_functions as edl

