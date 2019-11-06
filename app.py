import requests
import json
from requests.compat import urljoin
from requests.auth import HTTPBasicAuth
import boto3
import os
import json

from utils.logging import logger as log
from utils.newrelic import MetricsClient

uri_path = os.environ.get('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI')
if uri_path:
    creds_json = requests.get('http://169.254.170.2' + uri_path)
    creds = json.loads(creds_json.text)

    client = boto3.client(
         'cloudwatch',
         region_name='us-east-1',
         aws_access_key_id=creds['AccessKeyId'],
         aws_secret_access_key=creds['SecretAccessKey'],
         aws_session_token=creds['Token'])
else:
    client = boto3.client("cloudwatch")

URL = os.environ.get("RABBIT_MQ_URL", 'http://localhost:15672')
log.info("Using default Admin URL %s", URL)

USERNAME = os.environ.get("RABBIT_MQ_USERNAME", "guest")
log.info("Using default USERNAME %s", USERNAME)

PASSWORD = os.environ.get("RABBIT_MQ_PASSWORD", "guest")

STAGE = os.environ.get("STAGE", "Production")

requestURL = urljoin(URL, '/api/queues')

def put_metric(metrics):
    client.put_metric_data(
        Namespace='Resource/RabbitMQ',
        MetricData=metrics
    )

mc = MetricsClient()

if __name__ == '__main__':
    total_messages = 0
    resp = requests.get(requestURL, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if resp.status_code == 200:
        queues = resp.json()
        count = 0
        metrics = []
        events = []
        for count, q in enumerate(queues, start=1):
            messages = q['messages']
            name = q['name']

            # celery's weird worker tracking thing
            if "pidbox" in name or "@" in name:
                continue

            if count % 10 == 0:
                put_metric(metrics)
                metrics = []
                mc.log_events(events)
                events = []

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
        log.info("Total messages: %s", total_messages)
    else:
        log.error('error', resp.status_code)
