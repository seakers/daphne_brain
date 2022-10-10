# Daphne Brain

The api which serves all of the Daphne interfaces

## AWS Deployment

- Registry `923405430231.dkr.ecr.us-east-2.amazonaws.com/brain`


### Commands


##### AWS Docker Login

`aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 923405430231.dkr.ecr.us-east-2.amazonaws.com`



##### Local

`docker-compose build`

`docker-compose up -d`

`dshell brain`

`. run.sh`



##### Dev

`docker build -f DockerfileDev -t apazagab/brain:latest .`

`docker run --network=daphne-network --name=brain apazagab/brain:latest`



##### Prod

`docker build -f DockerfileProd -t 923405430231.dkr.ecr.us-east-2.amazonaws.com/brain:latest .`

`docker push 923405430231.dkr.ecr.us-east-2.amazonaws.com/brain:latest`









## Installation Instructions

1. Clone the repository or download a zip file of the last commit (https://help.github.com/articles/cloning-a-repository/)

2. Install python3 on the system if not in it yet (https://www.python.org/downloads/ or use packet manager if in Linux)

3. Create a python 3 virtual environment inside the cloned folder (http://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/)

### If using the historian skill:

4. Install the latest PostgreSQL on the system if not in it yet (https://www.postgresql.org/download/ or use a packet manager if in Linux)

### If using iFEED:

5. Install the latest version of Java Development Kit (JDK) if not in it yet (http://www.oracle.com/technetwork/java/javase/downloads/index-jsp-138363.html or use a packet manager if using Linux)



## Docker Compose Use

1. start the containers with `docker-compose up`

2. index the historian database with

    - `docker exec -it historian_db bash`
    - `scrapy crawl ceosdb_scraper`
    
3. create command models with 

    - `docker exec -it command_classifier bash`
    - `python3 question_generator.py`
    - `python3 train.py`
    - `exit`
    - `docker cp command_classifier:/app/command_classifier/models ./dialogue`



