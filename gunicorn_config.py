import json
import os

from pythonjsonlogger.jsonlogger import JsonFormatter

# https://docs.gunicorn.org/en/stable/settings.html#backlog

backlog = int(os.getenv("GUNICORN_BACKLOG", "2048"))

# https://docs.gunicorn.org/en/stable/settings.html#worker-processes

workers = int(os.getenv("GUNICORN_WORKERS", "5"))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gevent")
worker_connections = int(os.getenv("GUNICORN_WORKER_CONNECTIONS", "1000"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "90"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "1"))
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "0"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "0"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))

# http://docs.gunicorn.org/en/stable/settings.html#logging


class CustomJsonFormatter(JsonFormatter):
    def format(self, record):
        """Formats a log record and serializes to json"""
        try:
            record.msg = json.loads(record.getMessage())
        except json.JSONDecodeError:
            pass

        return super().format(record)


logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "()": CustomJsonFormatter,
            "format": "%(levelname)-8s [%(asctime)s] [%(request_id)s] %(name)s: %(message)s",
        }
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
        "error_console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "loggers": {
        "gunicorn.error": {"handlers": ["error_console"], "level": "INFO", "propagate": False},
        "gunicorn.access": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

errorlog = "-"
loglevel = "info"
accesslog = "-"
access_log_format = (
    '{"message": "%(r)s", "request_id": "%({HTTP_X_REQUEST_ID}o)s",'
    '"http_status": %(s)s, "ip_address": "%(h)s", "response_length": "%(b)s",'
    '"referer": "%(f)s", "user_agent": "%(a)s", "request_time": %(L)s, "date": "%(t)s"}'
)
