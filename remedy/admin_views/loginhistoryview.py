"""
loginhistoryview.py

Contains an administrative view for viewing login history.
"""
from admin_helpers import *

from flask.ext.admin.contrib.sqla import ModelView

from remedy.rad.models import LoginHistory


class LoginHistoryView(AdminAuthMixin, ModelView):
    """
    An administrative view for viewing login history.
    """
    # Disable creation/editing/deletion
    can_create = False
    can_delete = False
    can_edit = False

    column_list = ('login_date', 'username', 'ip', 'successful', 
        'failure_reason')

    column_default_sort = ('login_date', True)

    column_searchable_list = ('username',)

    column_filters = ('login_date', 'username', 'ip', 'successful', 
        'failure_reason',)

    column_labels = {
        'ip': 'IP'
    }

    column_choices = {'failure_reason': [
        ('No User', 'No User'),
        ('Bad Password', 'Bad Password'),
        ('Deactivated', 'Deactivated'),
        ('Not Confirmed', 'Not Confirmed'),
    ]}

    def __init__(self, session, **kwargs):
        super(LoginHistoryView, self).__init__(LoginHistory, session, **kwargs)    

