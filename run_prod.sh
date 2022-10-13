#!/bin/sh

###################
### FCGI METHOD ###
###################



# --> 2. Restart supervisorctl
if [ "$(supervisorctl pid)" != "unix:///var/run/supervisor.sock no such file" ]; then
    . /app/stop.sh
    kill -s SIGTERM $(supervisorctl pid)
fi


# --> 3. Create logs dir if DNE
if [ ! -d /app/logs ]; then
  echo "CREATING DIR"
  mkdir -p /app/logs;
else
  echo "DIR EXISTS"
fi


# --> 4. Set supervisord.conf file environment
INIT_SUPERVISOR="true"
if [ "$INIT_SUPERVISOR" = "true" ]; then
    cd /app
    BRAIN_ENV=$(cat .env_prod | sed 's|=\([^\n\r]*\)|="\1"|' | tr '\r' ',' | tr -d '\n')
    sed -i "s|^environment=.*|environment=$BRAIN_ENV,PYTHONUNBUFFERED=\"1\"|" /etc/supervisor/supervisord.conf
    sed -i "s|^directory=.*|directory=/app|" /etc/supervisor/supervisord.conf
    supervisord -c /etc/supervisor/supervisord.conf
fi


# --> 5. Start brain
supervisorctl start brain:*


echo 'SLEEP'
sleep 10s
echo 'FINISHED SLEEPING, TAIL'


# --> 6. Tail the output log file
tail -F /app/logs/brain.out.log /app/logs/brain.err.log /app/logs/daphne.log