import requests
import logging
import os
logger = logging.getLogger('monitor-rabbitmq')

STAGE = os.environ.get("STAGE", "prod")
METRIC_HOST = os.environ.get("METRIC_API_HOST")

class MetricsClient():

    SERVICE_NAME = 'ProdAnalyticsApi' \
        if STAGE == 'prod' \
        else 'StageAnalyticsApi'

    @staticmethod
    def log_event(event, destination='newrelic'):
        return MetricsClient.log_events([event], destination)

    @staticmethod
    def log_events(events=None, destination='newrelic'):
        events = events or []

        if METRIC_HOST:
            metric_event_url = '{url}/event'.format(url=METRIC_HOST)

            payload = dict(
                service=MetricsClient.SERVICE_NAME,
                publish=destination,
                events=events
            )

            try:
                response = requests.post(metric_event_url, json=payload)
                if not response.status_code == 200:
                    logger.warning(response)
                    logger.warning(response.content)
                response.raise_for_status()

            except Exception as e:
                # Non-critical metric logging
                # Never terminate upstream processes because of this

                logging.error(
                    "Failed to publish events to metric-api because: {reason}".format(
                        reason=e
                    ))

                return False
            else:
                return True
        else:
            return False

    @staticmethod
    def create_event(name='Unknown Api Event', tag='unknown-api-event', meta=dict()):
        return dict(name=name, tag=tag, meta=meta)

