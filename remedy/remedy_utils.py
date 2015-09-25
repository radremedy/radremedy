"""
remedy_utils.py

Contains miscellaneous utility functions.
"""
from jinja2 import Markup, escape
from jinja2.utils import urlize

from flask import request, flash, get_flashed_messages

from wtforms.validators import Length, URL, Email, NumberRange

import re

# This normalizes multiple contiguous nelines into discrete paragraphs.
_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

# This normalizes parentheses (like in area codes),
# dashes, and whitespace. The + is used to handle
# multiple contiguous items such as "(555) 555-5555"
_phone_re = re.compile(r'(?:\(|\)|\-|\s)+')


def flash_errors(form):
    """
    Flashes errors for the provided form.

    Args:
        form: The form for which errors will be displayed.
    """
    for field, errors in form.errors.items():
        for error in errors:
            flash("%s - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')


# Maps flashed message categories to the equivalent Bootstrap
# contextual alert class.
flash_message_classes = {
    'error': 'alert-danger',
    'danger': 'alert-danger',
    'warning': 'alert-warning',
    'success': 'alert-success',
    'info': 'alert-info',
    'message': 'alert-info'
}


def get_grouped_flashed_messages():
    """
    Gets the current set of flashed messages and returns them
    grouped by the appropriate Bootstrap contextual alert class.

    Returns:
        A dictionary of all messages, keyed by the appropriate
        Bootstrap contextual alert class.
    """
    # This will contain the lists of flashed messages,
    # keyed by the appropriate contextual Bootstrap class.
    grouped_messages = {
    }

    # Go through the messages
    for category, message in get_flashed_messages(with_categories=True):
        # Try to figure out the contextual class, defaulting to 'alert-info'.
        alert_class = flash_message_classes.get(category, 'alert-info')

        # Set up a list value for the relevant list class if not found.
        if alert_class not in grouped_messages:
            grouped_messages[alert_class] = list()

        grouped_messages[alert_class].append(message)

    return grouped_messages


def get_nl2br(value, make_urls=True):
    """
    Splits the provided string into paragraph tags based on the
    line breaks within it and returns the escaped result.

    Args:
        value: The string to process.
        make_urls: If True, will attempt to convert any URLs
            in the string to full links.

    Returns:
        The processed, escaped string.
    """
    # We need to surround each split paragraph with a <p> tag,
    # because otherwise Jinja ignores the result. See the PR for #254.
    if make_urls:
        return u'\n\n'.join(
            u'<p>%s</p>' %
            urlize(p, nofollow=True, target='_blank').
            replace('\n', Markup('<br>\n'))
            for p in _paragraph_re.split(escape(value)))
    else:
        return u'\n\n'.join(
            u'<p>%s</p>' %
            p.replace('\n', Markup('<br>\n'))
            for p in _paragraph_re.split(escape(value)))


def get_phoneintl(value):
    """
    Normalizes the provided phone number to a suitable
    international format.

    Args:
        eval_ctx: The context used for filter evaluation.
        value: The string to process.

    Returns:
        The processed phone number.
    """
    # Normalize whitespace, parens, and dashes to all be dashes
    result = u'-'.join(n for n in _phone_re.split(value.strip()))

    # Strip out any leading/trailing dashes
    result = result.strip(u'-')

    # See if we have an international country code
    if result[0] != u'+':
        # We don't - also see if we don't have the US code specified
        if result[0] != u'1':
            # Include the plus, the US code, and a trailing dash
            result = u'+1-' + result
        else:
            # Already have a country code - just add the plus
            result = u'+' + result

    return result


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
        elif isinstance(val, Email):
            field_args['type'] = 'email'
        elif isinstance(val, URL):
            field_args['type'] = 'url'
        elif isinstance(val, NumberRange):
            if val.min is not None:
                field_args['min'] = val.min
            if val.max is not None:
                field_args['max'] = val.max

    # If we have a description, create an aria-described by attribute
    if field.description and len(field.description) > 0:
        field_args['aria-describedby'] = field.id + '_help'

    # Merge in extra arguments
    field_args.update(kwargs)

    # Default rows for textareas if not specified
    if 'rows' not in field_args and field.type == 'TextAreaField':
        field_args['rows'] = '3'

    return field_args
