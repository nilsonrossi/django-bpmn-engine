import os

from distutils.util import strtobool


def eval_env_as_boolean(varname, standard_value):
    return strtobool(os.getenv(varname, standard_value))


def getenv_or_raise_exception(varname: str) -> str:
    """
    Retrieve a environment variable that MUST be set!
    """

    env = os.getenv(varname)
    if env is None:
        raise EnvironmentError(f"Environment variable {varname} is not set!")
    return env


def eval_env_as_integer(varname, standard_value):
    return int(os.getenv(varname, standard_value))


def eval_env_as_float(varname, standard_value):
    return float(os.getenv(varname, standard_value))


def convert_form_dict_to_json_schema(instance):
    map_type = {
        "string": "string",
        "boolean": "boolean",
        "long": "numbers",
        "enum": "string",
        "date": "string"
    }
    field_schema = {
        "type": 'object',
        "keys": {}
    }
    for field in instance.form_fields["fields"]:
        field_id = field["id"]
        field_schema["keys"][field_id] = {
            "type": map_type[field["type"]],
            "title": field["label"]
        }
        if field["type"] == "date":
            field_schema["keys"][field_id]["format"] = "date-time"
        if field["type"] == "enum":
            choices = []
            for opt in field["options"]:
                choices.append({"title": opt["name"], "value": opt["id"]})
            field_schema["keys"][field_id]["choices"] = choices
    return field_schema
