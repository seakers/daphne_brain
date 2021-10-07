from asgiref.sync import SyncToAsync, sync_to_async
from auth_API.helpers import get_or_create_user_information, get_user_information
from daphne_context.models import UserInformation

# Only use this function when your sync function does not do Django ORM calls! Or any other Django stuff
def sync_to_async_mt(func):
    return SyncToAsync(func, thread_sensitive=False)

@sync_to_async
def _get_user_information(session, user) -> UserInformation:
    return get_user_information(session, user)

@sync_to_async
def _get_or_create_user_information(session, user) -> UserInformation:
    return get_or_create_user_information(session, user)

@sync_to_async
def _save_subcontext(user_info: UserInformation, subcontext):
    getattr(user_info, subcontext).save()

@sync_to_async
def _save_user_info(user_info: UserInformation):
    user_info.save()