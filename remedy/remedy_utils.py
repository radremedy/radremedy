"""
remedy_utils.py

Contains miscellaneous utility functions.
"""
from flask import request
from wtforms.validators import Length

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

def get_field_args(field, **kwargs):
    """
    Generates a dictionary of arguments to be used when
    rendering out a form field.

    Args:
        field: The form field to render.
        **kwargs: Any additional arguments to include for the form field.

    Returns:
        A dictionary of arguments to use to render out a form field.
    """
    # Set up our default args
    field_args = {
        "class_": "form-control"
    }

    # Handle required fields
    if field.flags.required:
        field_args['required'] = 'required'

    # Look at field validators
    for val in field.validators:
        # Handle minlength/maxlength attributes if specified on
        # string fields through a Length validator    
        if isinstance(val, Length):
            if val.min > 0:
                field_args['minlength'] = val.min
            if val.max > 0:
                field_args['maxlength'] = val.max

    # If we have a description, create an aria-described by attribute
    if field.description and len(field.description) > 0:
        field_args['aria-describedby'] = field.id + '_help'

    # Merge in extra arguments
    field_args.update(kwargs)

    # Default rows for textareas if not specified
    if 'rows' not in field_args and field.type == 'TextAreaField':
        field_args['rows'] = '3'

    return field_args

