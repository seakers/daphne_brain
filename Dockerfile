FROM python:3.8-slim-buster



# --> 0. Preliminary Updates
RUN apt-get -y update &&\
    apt-get -y install build-essential manpages-dev

# --> 1. Copy Brain
WORKDIR /app
COPY ./. /app

# --> 2. Create Logs / Models
WORKDIR /app/logs
RUN touch /app/logs/daphne.logs
WORKDIR /app/dialogue/models

# --> 3. Install Requirements + Environment
WORKDIR /app
RUN pip3 install --no-cache-dir -r ./requirements.txt
RUN spacy download en_core_web_sm

# --> 4. Ensure Django Migrations are Applied (DEPRECATED)
#RUN python3 manage.py migrate --run-syncdb

# --> 5. Run app
RUN chmod +x /app/run.sh
CMD /app/run.sh