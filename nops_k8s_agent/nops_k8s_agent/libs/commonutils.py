import json

from loguru import logger

secs_per_min = 60.0
secs_per_hour = 3600.0
secs_per_day = 86400.0
mins_per_hour = 60.0
mins_per_day = 1440.0
hours_per_day = 24.0
hours_per_month = 730.0
days_per_month = 30.42


def duration_string(duration: int) -> str:
    duration_seconds = duration
    logger.info(duration_seconds)
    duration_str = ""
    duration_seconds = int(duration_seconds)
    logger.info(duration)
    if duration_seconds > 0:
        if duration_seconds % secs_per_day == 0:
            duration_str = "{}d".format(duration_seconds / secs_per_day)
        elif duration_seconds % secs_per_hour == 0:
            duration_str = "{}h".format(duration_seconds / secs_per_hour)
        elif duration_seconds % secs_per_min == 0:
            duration_str = "{}h".format(duration_seconds / secs_per_min)
        elif duration_seconds > 0:
            duration_str = "{}s".format(duration_seconds)
    logger.info(duration_str)
    return duration_str


def is_json(input):
    try:
        json.loads(input)
    except ValueError:
        return False
    return True
