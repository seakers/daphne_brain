from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
import re, datetime
import dateparser

from . import models

regexps = [
    r'when was (mission|instrument) (.*?) launched'
]

def ask_question(question):
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()

    match = None
    for regexp in regexps:
        match = re.match(regexp, question, re.I)
        if match is not None:
            break

    result = []
    if match is not None:
        date_parsing_settings = {'RELATIVE_BASE': datetime.datetime(2020, 1, 1)}
        try:
            # query = session.query(models.Mission)
            # date = dateparser.parse(match.group(2), settings=date_parsing_settings)
            # if match.group(1) == 'later':
            #     query = query.filter(models.Mission.launch_date > date).order_by(models.Mission.launch_date)
            # else:
            #     query = query.filter(models.Mission.launch_date < date).order_by(models.Mission.launch_date.desc())
            # query = query.order_by(models.Mission.launch_date)
            # for mission in query.all():
            #     result.append(mission.name)
            if match.group(1) == 'mission':
                query = session.query(models.Mission).filter(func.lower(models.Mission.name) == match.group(2))
                result.append(str(query.first().launch_date))
            else:
                query = session.query(models.Instrument).filter(func.lower(models.Instrument.name) == match.group(2))
                result.append(str(query.first().missions[0].launch_date))
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    print('The result is', result)

    if not result:
        return ['No answer']

    return result
