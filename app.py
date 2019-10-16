import requests
from requests.compat import urljoin
from requests.auth import HTTPBasicAuth
import boto3
import os
from utils.logging import logger as log

client = boto3.client('cloudwatch')

URL = os.environ.get("RABBIT_MQ_URL", 'http://localhost:15672')
log.info("Using default Admin URL %s", URL)

USERNAME = os.environ.get("RABBIT_MQ_USERNAME", "guest")
log.info("Using default USERNAME %s", USERNAME)

PASSWORD = os.environ.get("RABBIT_MQ_PASSWORD", "guest")

requestURL = urljoin(URL, '/api/queues')


def put_metric(metrics):
    client.put_metric_data(
        Namespace='Resource/RabbitMQ',
        MetricData=metrics
    )


if __name__ == '__main__':
    total_messages = 0
    resp = requests.get(requestURL, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if resp.status_code == 200:
        queues = resp.json()
        count = 0
        metrics = []
        for q in queues:
            messages = q['messages']
            name = q['name']
            count = count + 1
            if count % 10 == 0:
                put_metric(metrics)
                metrics = []
                count = 0
            metrics.append({
                    'MetricName': name,
                    'Dimensions': [
                        {
                            'Name': 'Resource',
                            'Value': 'RabbitMQ'
                        },
                    ],
                    'Value': messages,
                    'Unit': 'Count',
                    'StorageResolution': 60
                })
            total_messages = total_messages + messages
        if len(metrics) > 0:
            put_metric(metrics)

        put_metric([
                {
                    'MetricName': 'TotalMessages',
                    'Dimensions': [
                        {
                            'Name': 'Resource',
                            'Value': 'RabbitMQ'
                        },
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
