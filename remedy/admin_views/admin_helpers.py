"""
admin_helpers.py

Contains helper classes and methods for administrative actions.
"""
from flask import redirect, url_for, escape, Markup
from flask.ext.login import current_user

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
    'notes': 'Admin Notes'
}

# Defines column descriptions to be shared between resource views.
resource_column_descriptions = {
    'npi': 'The National Provider Identifier (NPI) of the resource.',
    'hours': 'The hours of operation for the resource.',
    'source': 'The source of the resource\'s information.',
    'notes': 'Administrative notes for the resource, not visible to end users.',
    'date_verified': 'The date the resource was last verified by an administrator.'
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

# Defines column formatters to be shared between resource views.
resource_column_formatters = {
    'submitted_user': submitted_user_column_formatter
}

# Intentionally blank to prevent link generation in CSV exports
resource_export_formatters = {
}

# Defines column formatters to be shared between review views.
review_column_formatters = {
    'user': review_user_column_formatter,
    'resource': review_resource_column_formatter
}

# Intentionally blank to prevent link generation in CSV exports
review_export_formatters = {
}