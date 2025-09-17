import re
import pandas as pd

def combine_dicts(group):
    combined_dict = {}
    for _, row in group.iterrows():
        combined_dict.update(row.dropna().to_dict())
    return combined_dict


def merge_lists_by_timestamp(dict_list):
    df = pd.DataFrame(dict_list)
    df['created_at'] = pd.to_datetime(df['created_at'])

    # Round the created_at values to the nearest minute
    df['created_at'] = df['created_at'].dt.round('min')
    return df.groupby('created_at').apply(combine_dicts).tolist()



def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if not parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def flatten_dict_list(dict_list, parent_key='', sep='_'):
    items = []
    for d in dict_list:
        if isinstance(d, dict):
            items.extend(flatten_dict(d, parent_key, sep=sep).items())
        else:
            items.append((parent_key, d))
    return dict(items)

def remove_timestamp(dict_):
    if "_created_at" in dict_:
        try:
            del dict_['_created_at']
        except Exception as err:
            print(err)
    return dict_



# test this function thoroughly
def expand_comma_values(data: dict):
    """
    Expands any comma-separated values in JSON strings.
    
    Args:
        json_list (list of str): List of JSON strings with one or more key-value pairs.
    
    Returns:
        list of str: List of JSON strings with expanded values.
    """
    expanded = []
    for key, value in data.items():
        if "," in value:
            values = [v.strip() for v in value.split(',')]  # strip whitespace
            expanded.extend({key: v} for v in values)
        else:
            expanded.append({key: value})
    return expanded




def dag_fields_to_exclude():
    return [
            "id",
            "timetable",
            "start_date",
            "end_date",
            "full_filepath",
            "template_searchpath",
            "template_undefined",
            "user_defined_macros",
            "user_defined_filters",
            "default_args",
            "concurrency",
            "max_active_tasks",
            "max_active_runs",
            "dagrun_timeout",
            "sla_miss_callback",
            "default_view",
            "orientation",
            "catchup",
            "on_success_callback",
            "on_failure_callback",
            "doc_md",
            "params",
            "access_control",
            "is_paused_upon_creation",
            "jinja_environment_kwargs",
            "render_template_as_native_obj",
            "tags",
            "owner_links",
            "auto_register",
            "fail_stop",
            "trigger_url_expected_response",
            "workflow",
        ]


def replace_url_kwargs(endpoint: str, params: dict | None = None) -> str:
    """
    Replace Django-style URL kwargs (<str:...>, <int:...>, etc.) with values from a dict.
    - If params is None or empty, return the endpoint unchanged (placeholders remain).
    """
    if not params:  # covers None or {}
        return endpoint

    pattern = re.compile(r"<(str|int|slug|uuid):(\w+)>")

    def replacer(match):
        _, key = match.group(1), match.group(2)  # converter, key
        if key not in params:
            return match.group(0)  # leave placeholder untouched
        return str(params[key])

    return pattern.sub(replacer, endpoint)



def path_to_regex(path_pattern: str) -> str:
    """
    Convert Django-style path string into regex.
    Example: /facebook/pages/<str:page_id>/ 
             -> ^/facebook/pages/(?P<page_id>[^/]+)/$
    """
    converters = {
        "str": r"[^/]+",
        "int": r"\d+",
        "slug": r"[-a-zA-Z0-9_]+",
        "uuid": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "path": r".+",
    }

    regex = path_pattern
    for conv, rgx in converters.items():
        regex = re.sub(
            rf"<{conv}:(\w+)>",
            lambda m: f"(?P<{m.group(1)}>{rgx})",  # function avoids escape issues
            regex
        )
    return f"^{regex}$"

def paths_match(request_path: str, db_path: str) -> bool:
    regex = path_to_regex(db_path)
    return bool(re.match(regex, request_path))
