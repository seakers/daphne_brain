FROM python:3.7-slim-stretch


RUN apt-get -y update &&\
    apt-get -y upgrade &&\
    apt-get -y install build-essential manpages-dev



# The working directory where daphne_brain is placed is /usr/src/app/daphne_brain
WORKDIR /app/daphne_brain

# Copy everything in the daphne_brain directory to /usr/src/app/daphne_brain
COPY ./. /app/daphne_brain/.

# Create logfile
WORKDIR /app/daphne_brain/logs
RUN touch daphne.logs

# Reset current directory
WORKDIR /app/daphne_brain

RUN pip3 install --no-cache-dir -r ./requirements.txt
RUN spacy download en

# Commands to start daphne_brain
#RUN python3 manage.py migrate --run-syncdb &&\
#    python3 manage.py collectstatic --clear --noinput