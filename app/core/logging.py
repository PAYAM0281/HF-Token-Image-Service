import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            log_record["timestamp"] = record.created
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


def setup_logging():
    log = logging.getLogger()
    log.setLevel(settings.LOG_LEVEL.upper())
    log.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)