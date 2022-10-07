FROM python:3.8-slim-buster



# --> 0. Preliminary Updates
RUN apt-get -y update &&\
    apt-get -y install build-essential manpages-dev

# --> 1. Copy Requiresments + Install
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r ./requirements.txt
RUN spacy download en_core_web_sm

# --> 2. Install Supervisor.d
WORKDIR /run/daphne
WORKDIR /etc/supervisor
RUN pip3 install --no-cache-dir supervisor
RUN mkdir /var/log/supervisor                 && \
    touch /var/log/supervisor/supervisord.log
COPY ./supervisord.conf  /etc/supervisor

# --> 3. Copy Brain + create dirs
WORKDIR /app
COPY ./. /app
WORKDIR /app/logs
RUN touch /app/logs/daphne.logs

# --> 4. Ensure Django Migrations are Applied (DEPRECATED)
#RUN python3 manage.py migrate --run-syncdb

# --> 5. Run app
WORKDIR /app
RUN chmod +x /app/run_prod.sh
CMD /app/run_prod.sh