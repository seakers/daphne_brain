FROM python:3.7-slim-stretch

# The working directory where daphne_brain is placed is /usr/src/app/daphne_brain
WORKDIR /usr/src/app/daphne_brain


# Copy everything in the daphne_brain directory to /usr/src/app/daphne_brain
COPY ./. /usr/src/app/daphne_brain/.


# Update apt-get package manager -- Install daphne_brain dependencies
RUN apt-get -y update &&\
    apt-get -y upgrade &&\
    apt-get -y install build-essential manpages-dev &&\
    pip3 install --no-cache-dir -r ./requirements.txt


# Commands to start daphne_brain
RUN python3 manage.py migrate --run-syncdb &&\
    python3 manage.py collectstatic --clear --noinput
CMD daphne -b 0.0.0.0 -p 8001 daphne_brain.asgi:application
