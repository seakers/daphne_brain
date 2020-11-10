from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from daphne_context.models import MycroftUser


# Django signals for creating mycroft code object
def create_mycroft_code(sender, instance, created):
    try:
        instance.mycroftuser
    except ObjectDoesNotExist:
        print("Creating mycroft user object")
        m = MycroftUser(user=instance)
        m.save()

post_save.connect(create_mycroft_code, sender=User)
