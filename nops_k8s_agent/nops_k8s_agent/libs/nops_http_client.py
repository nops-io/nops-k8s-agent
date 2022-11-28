import json
import logging
import time
from concurrent.futures import as_completed

from django.conf import settings

from requests_futures.sessions import FuturesSession

logger = logging.getLogger()


NOPS_MAX_WORKERS = 20


class RetriableException(Exception):
    pass


class NopsHTTPClient(object):
    _POST = "POST"
    _HEADERS = {"Content-type": "application/json"}

    def __init__(self, host, port, no_ssl, skip_ssl_validation, api_key, account_number, scrubber, timeout=10):
        self._HEADERS.update({"x-nops-api-key": api_key})
        self._HEADERS.update({"x-aws-account-number": str(account_number)})
        protocol = "http" if no_ssl else "https"
        self._url = "{}://{}:{}/svc/event_collector/v1/kube_collector".format(protocol, host, port)
        self._scrubber = scrubber
        self._timeout = timeout
        self._session = None
        self._ssl_validation = not skip_ssl_validation
        self._futures = []
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Initialized http client for logs intake: "
                f"<host: {host}, port: {port}, url: {self._url}, no_ssl: {no_ssl}, "
                f"skip_ssl_validation: {skip_ssl_validation}, timeout: {timeout}>"
            )

    def _connect(self):
        self._session = FuturesSession(max_workers=NOPS_MAX_WORKERS)
        self._session.headers.update(self._HEADERS)

    def _close(self):
        # Resolve all the futures and log exceptions if any
        for future in as_completed(self._futures):
            try:
                result = future.result()
                if result.status_code != 200:
                    location = result.headers.get("Location")
                    logger.exception(
                        f"Exception: Invalid response, status code: {result.status_code}, location: {location}\n"
                        f"Response content: \n{result.text}"
                    )
            except Exception:
                logger.exception("Exception while forwarding logs")

        self._session.close()

    def send(self, logs):
        """
        Sends a batch of log, only retry on server and network errors.
        """
        # FuturesSession returns immediately with a future object
        data = "[{}]".format(",".join(logs))
        future = self._session.post(
            self._url, data, timeout=self._timeout, verify=self._ssl_validation, allow_redirects=False
        )
        self._futures.append(future)

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, ex_type, ex_value, traceback):
        self._close()


class NopsClient(object):
    """
    Client that implements a exponential retrying logic to send a batch of logs.
    """

    def __init__(self, client, max_backoff=30):
        self._client = client
        self._max_backoff = max_backoff

    def send(self, logs):
        backoff = 1
        while True:
            try:
                self._client.send(logs)
                return
            except RetriableException:
                time.sleep(backoff)
                if backoff < self._max_backoff:
                    backoff *= 2
                continue

    def __enter__(self):
        self._client.__enter__()
        return self

    def __exit__(self, ex_type, ex_value, traceback):
        self._client.__exit__(ex_type, ex_value, traceback)


def filter_logs(logs, include_pattern=None, exclude_pattern=None):
    """
    Applies log filtering rules.
    If no filtering rules exist, return all the logs.
    """
    if include_pattern is None and exclude_pattern is None:
        return logs
    # Add logs that should be sent to logs_to_send
    logs_to_send = []
    for log in logs:
        logs_to_send.append(log)
    return logs_to_send


class NopsBatcher(object):
    def __init__(self, max_item_size_bytes, max_batch_size_bytes, max_items_count):
        self._max_item_size_bytes = max_item_size_bytes
        self._max_batch_size_bytes = max_batch_size_bytes
        self._max_items_count = max_items_count

    def _sizeof_bytes(self, item):
        return len(str(item).encode("UTF-8"))

    def batch(self, items):
        """
        Returns an array of batches.
        Each batch contains at most max_items_count items and
        is not strictly greater than max_batch_size_bytes.
        All items strictly greater than max_item_size_bytes are dropped.
        """
        batches = []
        batch = []
        size_bytes = 0
        size_count = 0
        for item in items:
            item_size_bytes = self._sizeof_bytes(item)
            if size_count > 0 and (
                size_count >= self._max_items_count or size_bytes + item_size_bytes > self._max_batch_size_bytes
            ):
                batches.append(batch)
                batch = []
                size_bytes = 0
                size_count = 0
            # all items exceeding max_item_size_bytes are dropped here
            if item_size_bytes <= self._max_item_size_bytes:
                batch.append(item)
                size_bytes += item_size_bytes
                size_count += 1
        if size_count > 0:
            batches.append(batch)
        return batches


def forward_logs(logs, aws_account_number):
    """Forward logs to nOps"""
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Forwarding {len(logs)} logs")

    logs_to_forward = filter_logs([json.dumps(log, default=str) for log in logs])
    batcher = NopsBatcher(512 * 1000, 4 * 1000 * 1000, 400)
    cli = NopsHTTPClient(
        settings.NOPS_K8S_COLLECTOR_HOST,
        settings.NOPS_K8S_COLLECTOR_PORT,
        settings.NOPS_K8S_COLLECTOR_NO_SSL,
        settings.NOPS_K8S_COLLECTOR_SKIP_SSL_VALIDATION,
        settings.NOPS_K8S_COLLECTOR_API_KEY,
        settings.NOPS_K8S_COLLECTOR_AWS_ACCOUNT_NUMBER,
        None,
    )

    with NopsClient(cli) as client:
        for batch in batcher.batch(logs_to_forward):
            try:
                client.send(batch)
            except Exception:
                logger.exception(f"Exception while forwarding log batch {batch}")
            else:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Forwarded log batch: {json.dumps(batch)}")
