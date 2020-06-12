import requests
import logging
import os
logger = logging.getLogger('monitor-rabbitmq')

STAGE = os.environ.get("STAGE", "prod")

class MetricsClient(object):

    NEWRELIC_ACCOUNT_ID = '1006333'
    NEWRELIC_INSERT_API_KEY = 'Q4UYiEoEPM5EvwscGyQXt6mWmEOG-2D7'
    NEWRELIC_QUERY_API_KEY = 'b8rPDYTYzW7yPm5y6--RZS7T_ToYoqwp'
    SERVICE = 'ProdAnalyticsApi' \
        if os.environ.get('STAGE') == 'prod' or os.environ.get('STAGE') == 'production' \
        else 'StageAnalyticsApi'

    @staticmethod
    def log_event(event):
        return MetricsClient.log_events([event])

    @staticmethod
    def create_event(name='Unknown Api Event', tag='unknown-api-event', meta=dict()):
        return dict(name=name, tag=tag, meta=meta)

    @classmethod
    def transform_to_nr_event(cls, event):
        event_name = event.get('name')
        event_tag = event.get('tag')
        event_meta = event.get('meta')

        nr_event = dict(
            eventType=cls.SERVICE,
            name=event_name,
            tag=event_tag
        )

        for key in event_meta:
            meta_key = 'meta_{key}'.format(key=key)

            meta_value = event_meta[key] \
                if isinstance(event_meta[key], str) or isinstance(event_meta[key], int) or isinstance(event_meta[key],
                                                                                                      float) \
                else str(event_meta[key])

            nr_event[meta_key] = meta_value

        return nr_event

    @classmethod
    def log_events(cls, events):

        newrelic_payload = list(map(cls.transform_to_nr_event, events))

        event_url = 'https://insights-collector.newrelic.com/v1/accounts/{account_id}/events'.format(
            account_id=cls.NEWRELIC_ACCOUNT_ID)

        headers = dict()
        headers['Content-Type'] = 'application/json'
        headers['X-Insert-Key'] = cls.NEWRELIC_INSERT_API_KEY

        try:
            response = requests.post(event_url, json=newrelic_payload, headers=headers, timeout=3)
            response.raise_for_status()

        except Exception as e:
            error_message = "Failed to publish for [{service}] with payload [{nr_payload}] because: {reason}".format(
                    service=cls.SERVICE, nr_payload=str(newrelic_payload), reason=str(e))

            return False, error_message
        else:
            return True, None

