"""
remedy_utils.py

Contains miscellaneous utility functions.
"""
from flask import request

def get_ip():
    """
    Attempts to determine the IP of the user making the request,
    taking into account any X-Forwarded-For headers.

    Returns:
        The IP of the user making the request, as a string.
    """
    if not request.headers.getlist("X-Forwarded-For"):
        return str(request.remote_addr)
    else:
        return str(request.headers.getlist("X-Forwarded-For")[0])
