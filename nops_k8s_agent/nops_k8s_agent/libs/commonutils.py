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


def check_str_is_json(item):
    try:
        return json.loads(item), True
    except ValueError:
        return item, False


def check_str_is_bool(item):
    return (item == "true", True) if item.lower() in ["true", "false"] else item, False


def flatten_dict(inp_dict, sep=".", exclude=[]):
    obj = {}

    def recurse(dict_node, parent_key=""):
        if isinstance(dict_node, dict):
            for k, v in dict_node.items():
                new_key = parent_key + sep + k if parent_key else k
                if new_key not in exclude:
                    recurse(v, new_key)
        else:
            if isinstance(dict_node, str):
                result, compliant = check_str_is_bool(dict_node)
                obj[parent_key] = result if compliant else check_str_is_json(dict_node)[0]
            else:
                obj[parent_key] = dict_node

    recurse(inp_dict)
    return obj
