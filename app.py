import requests
import json
from requests.compat import urljoin
from requests.auth import HTTPBasicAuth
import boto3
import os
import json
import logging
import time
import datetime

from utils.newrelic import MetricsClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = boto3.client("cloudwatch", "us-east-1")

URL = os.environ.get("RABBIT_MQ_URL", 'http://localhost:15672')
logger.info("Using Admin URL %s", URL)

USERNAME = os.environ.get("RABBIT_MQ_USERNAME", "guest")
logger.info("Using USERNAME %s", USERNAME)

PASSWORD = os.environ.get("RABBIT_MQ_PASSWORD", "guest")

STAGE = os.environ.get("STAGE", "Production")

requestURL = urljoin(URL, '/api/queues')

def put_metric(metrics):
    client.put_metric_data(
        Namespace='Resource/RabbitMQ',
        MetricData=metrics
    )

mc = MetricsClient()

def process_queue():
    total_messages = 0
    resp = requests.get(requestURL, auth=HTTPBasicAuth(USERNAME, PASSWORD))

    if os.environ.get("DEBUG"):
        logger.setLevel(logging.DEBUG)

    if resp.status_code == 200:
        queues = resp.json()
        logger.info("Checking %d queues", len(queues))
        count = 0
        metrics = []
        events = []
        for q in queues:
            messages = q['messages']
            name = q['name']

            # celery's weird worker tracking thing
            if "pidbox" in name or "@" in name:
                continue
            count += 1

            if len(metrics) >= 10:
                put_metric(metrics)
                metrics = []
                mc.log_events(events)
                events = []

            logger.debug("Queue: %s Messages %d", name, messages)
            metrics.append({
                    'MetricName': name,
                    'Dimensions': [
                        {
                            'Name': 'Resource',
                            'Value': 'RabbitMQ'
                        },
                        {
                            'Name': 'Environment',
                            'Value': STAGE
                        }
                    ],
                    'Value': messages,
                    'Unit': 'Count',
                    'StorageResolution': 60
                })

            q['Environment'] = STAGE

            events.append(mc.create_event(
                name='RabbitMQCount',
                tag=name,
                meta=q
            ))

            total_messages = total_messages + messages
        else:
            if metrics:
                put_metric(metrics)

            if events:
                mc.log_events(events)

        put_metric([
                {
                    'MetricName': 'TotalMessages',
                    'Dimensions': [
                        {
                            'Name': 'Resource',
                            'Value': 'RabbitMQ'
                        },
                        {
                            'Name': 'Environment',
                            'Value': STAGE
                        }
                    ],
                    'Value': total_messages,
                    'Unit': 'Count',
                    'StorageResolution': 60
                },
            ]
        )
        logger.info("Queues written: %d, Total messages: %s", count, total_messages)
    else:
        logger.error('error', resp.status_code)

if __name__ == "__main__":
    while True:
        process_queue()
        dt = datetime.datetime.now()
        dt = (dt + datetime.timedelta(seconds=60)).replace(second=0, microsecond=0)
        total_seconds = (dt - datetime.datetime.now()).total_seconds()
        time.sleep(total_seconds)