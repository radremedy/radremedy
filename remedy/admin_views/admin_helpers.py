"""
admin_helpers.py

Contains helper classes and methods for administrative actions.
"""
from urllib import quote

from flask import redirect, url_for, escape, Markup
from flask.ext.login import current_user

from remedy.remedy_utils import get_nl2br


def nl2br_formatter(value, make_urls=True):
    """
    Formats the provided value to convert newlines to line breaks.

    Args:
        value: The string value to format.
        make_urls: If true, will attempt to auto-link URLs
            detected in the string.

    Returns:
        The formatted, escaped HTML for the string.
    """
    if value and len(value) > 0 and not value.isspace():
        return Markup(get_nl2br(value, make_urls=make_urls))
    else:
        return ""


def html_formatter(value):
    """
    Formats the provided value to return HTML.

    Args:
        value: The string value to format.

    Returns:
        The raw string value, marked as safe.
    """
    if value and len(value) > 0 and not value.isspace():
        return Markup(value)
    else:
        return ""


def submitted_user_column_formatter(view, context, model, name):
    """
    A column formatter to be used for Resource.submitted_user values.
    """
    if model.submitted_user is not None:
        return get_user_link(model.submitted_user)
    else:
        return ""


def review_user_column_formatter(view, context, model, name):
    """
    A column formatter to be used for Review.user values.
    """
    if model.user is not None:
        return get_user_link(model.user)
    else:
        return ""


def review_resource_column_formatter(view, context, model, name):
    """
    A column formatter to be used for Review.resource values.
    """
    if model.resource is not None:
        return get_resource_link(model.resource)
    else:
        return ""


def resourceimport_redirect():
    """
    Returns a redirection action to the main resource importing view,
    which is a list of files available for importing.

    Returns:
        The redirection action.
    """
    return redirect(url_for('resourceimportfilesview.index'))


def get_resource_link(resource):
    """
    Gets a properly-escaped link to the resource.

    Args:
        resource: The resource to link to.

    Returns:
        A properly-escaped link to the resource.
    """
    return Markup(u'<a href="%s" target="_blank">%s</a>' % (
        url_for('resourceview.details_view', id=resource.id),
        escape(resource.name)))


def get_user_link(user):
    """
    Gets a properly-escaped link to the user.

    Args:
        user: The user to link to.

    Returns:
        A properly-escaped link to the user.
    """
    return Markup(u'<a href="%s" target="_blank">%s</a>' % (
        url_for('userview.details_view', id=user.id),
        escape(user.username)))


def get_email_link(user, subject=None):
    """
    Gets a properly-escaped link to email the user.

    Args:
        user: The user to email.
        subject: The subject to use. Optional.

    Returns:
        A properly-escaped link to email the user.
    """
    if subject and len(subject) > 0 and not subject.isspace():
        subject = unicode('?subject=' + quote(subject))
    else:
        subject = u''

    return Markup(u'<a href="mailto:%s%s">%s</a>' % (
        Markup(quote(user.email)),
        subject,
        escape(user.email)))


class AdminAuthMixin(object):
    """
    A mixin for ensuring that only logged-in administrators
    can access Admin views.
    """
    def is_accessible(self):
        """
        Determines if the current user is logged in as an admin.

        Returns:
            A boolean indicating if the current user is an admin.
        """
        if current_user.is_authenticated and current_user.admin:
            return True

        return False


# Defines column labels to be shared between resource views.
resource_column_labels = {
    'id': 'ID',
    'npi': 'NPI',
    'url': 'URL',
    'is_icath': 'Informed Consent/ICATH',
    'is_wpath': 'WPATH',
    'is_accessible': 'ADA/Wheelchair Accessible',
    'has_sliding_scale': 'Sliding Scale',
    'is_approved': 'Approved',
    'submitted_user': 'Submitted User',
    'submitted_ip': 'Submitted IP',
    'submitted_date': 'Submitted Date',
    'notes': 'Admin Notes',
    'advisory_notes': 'Advisory Notes'
}

# Defines column descriptions to be shared between resource views.
resource_column_descriptions = {
    'name':
        'Formatting: First Name Last Name, Titles ' +
        '(ex. Jane Smith, LCSW)\n\n' +
        'If this is an organization, please put its name in this box.',
    'npi': 'The National Provider Identifier (NPI) of the resource.',
    'phone': 'Formatting: (555) 555-5555',
    'fax': 'Formatting: (555) 555-5555',
    'hours': 'The hours of operation for the resource.\n\n' +
        'Specific Formatting: Days: Mon, Tues, Wed, Thurs, Fri, Sat, Sun; ' +
        'Hours: 9 am - 4:30 pm. Extra Specifics: (Walk-ins)\n\n' +
        'Long Formatting Example: Mon, Tues, Wed - 9 am - 4:30 pm ' +
        '(By Appointment Only); Thurs-Sat - 10:30 am - 7 pm ' +
        '(Appointments and Walk-ins); Sun - Closed',
    'source': 'The source of the resource\'s information.',
    'notes':
        'Administrative notes for the resource, not visible to end users.',
    'advisory_notes':
        'Publicly-visible advisories for the resource.',
    'date_verified':
        'The date the resource was last verified by an administrator.'
}

# Defines column labels to be shared between review views
review_column_labels = {
    'id': 'ID',
    'composite_rating': 'Comp. Rating',
    'rating': 'Provider Rating',
    'staff_rating': 'Staff Rating',
    'intake_rating': 'Intake Rating',
    'text': 'Review Text',
    'resource.name': 'Resource',
    'resource_id': 'Resource',
    'user.username': 'User',
    'user_id': 'User',
    'visible': 'Visible',
    'date_created': 'Date Created',
    'ip': 'IP'
}

# Defines column descriptions to be shared between review views.
review_column_descriptions = {
    'composite_rating': 'The average of the rating fields.'
}


# Defines column labels to be shared between category/population views.
catpop_column_labels = {
    'id': 'ID',
    'grouping': 'Group',
    'date_created': 'Date Created'
}

# Defines column descriptions to be shared between category/population views.
catpop_column_descriptions = {
    'keywords':
        'The keywords used to search for the item, separated by spaces ' +
        'or newlines. Include synonyms and item specializations.'
}

# Defines column labels to be shared between category/population group views.
group_column_labels = {
    'id': 'ID',
    'grouporder': 'Order',
    'date_created': 'Date Created'
}

# Defines column descriptions to be shared between
# category/population group views.
group_column_descriptions = {
}

# Defines column labels to be shared between news post views.
news_column_labels = {
    'id': 'ID',
    'date_created': 'Date Created'
}

# Defines column descriptions to be shared between news post views.
news_column_descriptions = {
    'author':
        'A free-text field indicating the author of the post.',
    'summary':
        'The summary for the news post, displayed in lists.',
    'body':
        'The rich-text body of the news post, displayed for the individual ' +
        'article.'
}

# Defines column formatters to be shared between resource views.
resource_column_formatters = {
    'submitted_user': submitted_user_column_formatter,
    'description': lambda v, c, m, p:
        nl2br_formatter(m.description),
    'hours': lambda v, c, m, p:
        nl2br_formatter(m.hours),
    'hospital_affiliation': lambda v, c, m, p:
        nl2br_formatter(m.hospital_affiliation),
    'source': lambda v, c, m, p:
        nl2br_formatter(m.source),
    'notes': lambda v, c, m, p:
        nl2br_formatter(m.notes),
    'advisory_notes': lambda v, c, m, p:
        nl2br_formatter(m.advisory_notes)
}

# Intentionally blank to prevent HTML in CSV exports
resource_export_formatters = {
}

# Defines column formatters to be shared between review views.
review_column_formatters = {
    'user': review_user_column_formatter,
    'resource': review_resource_column_formatter,
    'text': lambda v, c, m, p:
        nl2br_formatter(m.text, make_urls=False)
}

# Intentionally blank to prevent HTML in CSV exports
review_export_formatters = {
}

# Defines column formatters to be shared between category/population views.
catpop_column_formatters = {
    'description': lambda v, c, m, p:
        nl2br_formatter(m.description),
    'keywords': lambda v, c, m, p:
        nl2br_formatter(m.keywords, make_urls=False)
}

# Intentionally blank to prevent HTML in CSV exports
catpop_export_formatters = {
}

# Defines column formatters to be shared between
# category/population group views.
group_column_formatters = {
    'description': lambda v, c, m, p:
        nl2br_formatter(m.description)
}

# Intentionally blank to prevent HTML in CSV exports
group_export_formatters = {
}

# Defines formatters to be used for news post views.
news_column_formatters = {
    'summary': lambda v, c, m, p:
        nl2br_formatter(m.summary),
    'body': lambda v, c, m, p:
        html_formatter(m.body)
}

# Intentionally blank to prevent HTML in CSV exports
news_export_formatters = {
}
