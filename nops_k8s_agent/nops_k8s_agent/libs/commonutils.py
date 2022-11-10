import json

secs_per_min = 60
secs_per_hour = 3600
secs_per_day = 86400


def duration_string(duration_seconds: int) -> str:
    duration_seconds = int(duration_seconds)
    if duration_seconds > 0:
        if duration_seconds % secs_per_day == 0:
            return "{}d".format(duration_seconds // secs_per_day)
        elif duration_seconds % secs_per_hour == 0:
            return "{}h".format(duration_seconds // secs_per_hour)
        elif duration_seconds % secs_per_min == 0:
            return "{}m".format(duration_seconds // secs_per_min)
        elif duration_seconds > 0:
            return "{}s".format(duration_seconds)
    return ""


def check_str_is_json(item):
    try:
        return json.loads(item), True
    except ValueError:
        return item, False


def check_str_is_bool(item):
    return (item == "true", True) if item.lower() in ["true", "false"] else item, False


def flatten_dict(inp_dict, sep=".", exclude=[], skip_parsing=False):
    obj = {}

    def recurse(dict_node, parent_key=""):
        if isinstance(dict_node, dict):
            for k, v in dict_node.items():
                new_key = parent_key + sep + k if parent_key else k
                if new_key not in exclude:
                    recurse(v, new_key)
        else:
            if isinstance(dict_node, str) and not skip_parsing:
                result, compliant = check_str_is_bool(dict_node)
                obj[parent_key] = result if compliant else check_str_is_json(dict_node)[0]
            else:
                obj[parent_key] = dict_node

    recurse(inp_dict)
    return obj
