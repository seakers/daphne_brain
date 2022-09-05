FROM python:3.8-slim-buster


# --> 0. Preliminary Updates
RUN apt-get -y update &&\
    apt-get -y install build-essential manpages-dev

# --> 1. Copy Brain
WORKDIR /app
COPY ./. /app

# --> 2. Create Logs
WORKDIR /app/logs
RUN touch /app/logs/daphne.logs

# --> 3. Install Requirements + Environment
WORKDIR /app
RUN pip3 install --no-cache-dir -r ./requirements.txt
RUN spacy download en_core_web_sm


# --> Config
ENV DAPHNEVERSION="EOSS"
ENV VASSAR_HOST="127.0.0.1"
ENV VASSAR_PORT="9090"
ENV DATAMINING_HOST="127.0.0.1"
ENV DATAMINING_PORT="9191"
ENV PYTHONUNBUFFERED="1"
ENV VASSAR_REQUEST_URL="https://sqs.us-east-2.amazonaws.com/923405430231/vassar_request"
ENV VASSAR_RESPONSE_URL="https://sqs.us-east-2.amazonaws.com/923405430231/vassar_response"
ENV GA_REQUEST_URL="https://sqs.us-east-2.amazonaws.com/923405430231/ga_request"
ENV GA_RESPONSE_URL="https://sqs.us-east-2.amazonaws.com/923405430231/ga_response"
ENV DEPLOYMENT_TYPE="aws"


# --> DBs
ENV SQL_USER="daphne"
ENV SQL_PASSWORD="xxxxxxxxxxxx"
ENV USER="daphne"
ENV PASSWORD="xxxxxxxxxxxx"
ENV POSTGRES_HOST="daphne-dev-database.csl99y1ur3jh.us-east-2.rds.amazonaws.com"
ENV POSTGRES_PORT="5432"


# --> Services
#ENV REDIS_HOST="redis.daphne.dev"
ENV REDIS_HOST="3.145.19.234"
ENV REDIS_PORT="6379"
#ENV RABBITMQ_HOST="rabbitmq.daphne.dev"
ENV RABBITMQ_HOST="3.21.28.35"
#ENV NEO4J_HOST="neo4j.daphne.dev"
ENV NEO4J_HOST="3.140.186.76"
ENV NEO4J_PORT="7687"
ENV NEO4J_USER="neo4j"
ENV NEO4J_PASSWORD="test"
#ENV HASURA_HOST="http://graphql.daphne.dev:8080/v1/graphql"
#ENV HASURA_HOST_WS="ws://graphql.daphne.dev:8080/v1/graphql"
ENV HASURA_HOST="http://3.16.50.181:8080/v1/graphql"
ENV HASURA_HOST_WS="ws://3.16.50.181:8080/v1/graphql"

ENV CLUSTER_ARN="arn:aws:ecs:us-east-2:923405430231:cluster/daphne-cluster"
ENV VASSAR_SERVICE_ARN="arn:aws:ecs:us-east-2:923405430231:service/daphne-cluster/evaluator-service"
ENV GA_SERVICE_ARN="arn:aws:ecs:us-east-2:923405430231:service/daphne-cluster/genetic-algorithm"



# --> 4. Ensure Django Migrations are Applied
#RUN python3 manage.py migrate --run-syncdb


#CMD daphne -b 0.0.0.0 -p 8000 daphne_brain.asgi:application