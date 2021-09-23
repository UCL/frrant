import os
from functools import wraps


def disable_for_loaddata(signal_handler):
    """
    Decorator that turns off signal handlers when loading fixture data.
    Looks at both the env variable and the 'raw' flag in the signal.
    NB the env variable is required as the 'raw' flag is not yet
    sent by Django for m2m changed signals :-/
    We check them both anyway.
    """

    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        # check the env variable here
        if os.environ.get("LOADING", None):
            return
        # check the raw flag (not there for m2m signals)
        if kwargs.get("raw"):
            return
        signal_handler(*args, **kwargs)

    return wrapper
