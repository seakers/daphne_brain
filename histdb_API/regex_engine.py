from sqlalchemy.orm import sessionmaker
import re, datetime
import dateparser

from . import models

regexps = [
    r'missions (later|earlier) than (\d+)'
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
            query = session.query(models.Mission)
            date = dateparser.parse(match.group(2), settings=date_parsing_settings)
            if match.group(1) == 'later':
                query = query.filter(models.Mission.launch_date > date).order_by(models.Mission.launch_date)
            else:
                query = query.filter(models.Mission.launch_date < date).order_by(models.Mission.launch_date.desc())
            query = query.order_by(models.Mission.launch_date)
            for mission in query.all():
                result.append(mission.name)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    print(result)
    if not result:
        return ['No answer']

    return result