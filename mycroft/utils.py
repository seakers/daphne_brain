import daphne_context
import random


def generate_unique_mycroft_session():
    current_sessions = get_current_mycroft_sessions()

    session = generate_mycroft_session()
    tries = 0
    while session in current_sessions:
        session = generate_mycroft_session()
        tries += 1
        if tries > 100:
            session
    return session


def get_current_mycroft_sessions():
    sessions = []
    entries = daphne_context.models.UserInformation.objects.all()
    for entry in entries:
        if entry.mycroft_session is not None:
            sessions.append(entry.mycroft_session)
    return sessions


def generate_mycroft_session():
    number = str(abs(random.randint(0, 9999)))
    while len(number) < 4:
        number = '0' + number
    return number



