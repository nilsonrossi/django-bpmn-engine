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
