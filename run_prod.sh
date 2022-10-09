#!/bin/sh

###################
### FCGI METHOD ###
###################

# --> 1. Restart supervisorctl
if [ "$(supervisorctl pid)" = "unix:///var/run/supervisor.sock no such file" ]; then
    echo '--> Supervisorclt not running... '
else
    . /app/stop.sh
    kill -s SIGTERM $(supervisorctl pid)
fi

# --> 2. Set supervisord.conf file environment
INIT_SUPERVISOR="true"
if [ "$INIT_SUPERVISOR" = "true" ]; then
    cd /app
    BRAIN_ENV=$(cat .env_prod | sed 's|=\([^\n\r]*\)|="\1"|' | tr '\r' ',' | tr -d '\n')
    sed -i "s|^environment=.*|environment=$BRAIN_ENV,PYTHONUNBUFFERED=\"1\"|" /etc/supervisor/supervisord.conf
    sed -i "s|^directory=.*|directory=/app|" /etc/supervisor/supervisord.conf
    supervisord -c /etc/supervisor/supervisord.conf
fi

# --> 3. Run brain
supervisorctl start brain:*

# --> 4. Tail the output log file
tail -f /app/logs/brain.out.log /app/logs/brain.err.log