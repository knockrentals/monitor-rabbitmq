#!/bin/sh

#remove hardlinks to allow cron to run
touch /etc/crontab /etc/cron.*/*
echo $AWS_CONTAINER_CREDENTIALS_RELATIVE_URI > /root/AWS_CONTAINER_CREDENTIALS_RELATIVE_URI
echo $RABBIT_MQ_URL > /root/RABBIT_MQ_URL
echo $RABBIT_MQ_USERNAME > /root/RABBIT_MQ_USERNAME
echo $RABBIT_MQ_PASSWORD > /root/RABBIT_MQ_PASSWORD

echo $ENVIRONMENT > /root/ENVIRONMENT
echo "* * * * * root PYTHONPATH=/usr/local/lib/python3.7/site-packages/ AWS_CONTAINER_CREDENTIALS_RELATIVE_URI=`cat /root/AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` RABBIT_MQ_URL=`cat /root/RABBIT_MQ_URL` RABBIT_MQ_USERNAME=`cat /root/RABBIT_MQ_USERNAME` RABBIT_MQ_PASSWORD=`cat /root/RABBIT_MQ_PASSWORD` /usr/local/bin/python /code/app.py >> /var/log/cron.log 2>&1
" >> /etc/cron.d/report-rabbitmq-status

# Hand off to the CMD
exec "$@"
