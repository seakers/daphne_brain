# from daphne_context.models import UserInformation
import random

def generate_mycroft_session():
    number = str(abs(random.randint(0, 9999)))
    while len(number) < 4:
        number = '0' + number
    return number


