"""
admin_helpers.py

Contains helper classes and methods for administrative actions.
"""
from flask import redirect, url_for
from flask.ext.login import current_user


def resourceimport_redirect():
    """
    Returns a redirection action to the main resource importing view, 
    which is a list of files available for importing.

    Returns:
        The redirection action.
    """
    return redirect(url_for('resourceimportfilesview.index'))

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
        if current_user.is_authenticated() and current_user.admin:
            return True

        return False
