#!/bin/sh

#remove hardlinks to allow cron to run
touch /etc/crontab /etc/cron.*/*
echo $AWS_CONTAINER_CREDENTIALS_RELATIVE_URI > /root/AWS_CONTAINER_CREDENTIALS_RELATIVE_URI
echo $ENVIRONMENT > /root/ENVIRONMENT
echo "* * * * * root PYTHONPATH=/usr/local/lib/python3.7/site-packages/ AWS_CONTAINER_CREDENTIALS_RELATIVE_URI=`cat /root/AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` ENVIRONMENT=`cat /root/ENVIRONMENT` python /code/app.py >> /var/log/cron.log 2>&1
" >> /etc/cron.d/report-idle-workers
service cron start

# Hand off to the CMD
exec "$@"

