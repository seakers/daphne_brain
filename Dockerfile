FROM python:3.8-slim-buster

# --> Config
ENV DAPHNEVERSION=${DAPHNEVERSION}
ENV VASSAR_HOST=${VASSAR_HOST}
ENV VASSAR_PORT=${VASSAR_PORT}
ENV DATAMINING_HOST=${DATAMINING_HOST}
ENV DATAMINING_PORT=${DATAMINING_PORT}
ENV PYTHONUNBUFFERED=${PYTHONUNBUFFERED}
ENV VASSAR_REQUEST_URL=${VASSAR_REQUEST_URL}
ENV VASSAR_RESPONSE_URL=${VASSAR_RESPONSE_URL}
ENV GA_REQUEST_URL=${GA_REQUEST_URL}
ENV GA_RESPONSE_URL=${GA_RESPONSE_URL}
ENV DEPLOYMENT_TYPE=${DEPLOYMENT_TYPE}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}

# --> DBs
ENV SQL_USER=${SQL_USER}
ENV SQL_PASSWORD=${SQL_PASSWORD}
ENV USER=${USER}
ENV PASSWORD=${PASSWORD}
ENV POSTGRES_HOST=${POSTGRES_HOST}
ENV POSTGRES_PORT=${POSTGRES_PORT}

# --> Services
ENV REDIS_HOST=${REDIS_HOST}
ENV REDIS_PORT=${REDIS_PORT}
ENV RABBITMQ_HOST=${RABBITMQ_HOST}
ENV NEO4J_HOST=${NEO4J_HOST}
ENV NEO4J_PORT=${NEO4J_PORT}
ENV NEO4J_USER=${NEO4J_USER}
ENV NEO4J_PASSWORD=${NEO4J_PASSWORD}
ENV HASURA_HOST=${HASURA_HOST}
ENV HASURA_HOST_WS=${HASURA_HOST_WS}
ENV CLUSTER_ARN=${CLUSTER_ARN}
ENV VASSAR_SERVICE_ARN=${VASSAR_SERVICE_ARN}
ENV GA_SERVICE_ARN=${GA_SERVICE_ARN}










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


RUN echo "alias runapp='daphne -b 0.0.0.0 -p 8000 daphne_brain.asgi:application'" >> ~/.profile
RUN source ~/.profile
CMD daphne -b 0.0.0.0 -p 8000 daphne_brain.asgi:application