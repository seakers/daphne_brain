#!/bin/sh

###################
### FCGI METHOD ###
###################


# --> 1. Set supervisord.conf file environment
INIT_SUPERVISOR="false"
if [ "$INIT_SUPERVISOR" = "true" ]; then
    cd /app
    BRAIN_ENV=$(cat .env | sed 's|=\([^\n\r]*\)|="\1"|' | tr '\r' ',' | tr -d '\n')
    sed -i "s|^environment=.*|environment=$BRAIN_ENV,PYTHONUNBUFFERED=\"1\"|" /etc/supervisor/supervisord.conf
    sed -i "s|^directory=.*|directory=/app|" /etc/supervisor/supervisord.conf
    supervisord -c /etc/supervisor/supervisord.conf
fi

# --> 2. Run Brain
supervisorctl start brain:*


##################
### OLD METHOD ###
##################

# env $(cat .env | tr -d '\r') daphne -b 0.0.0.0 -p 8000 daphne_brain.asgi:application