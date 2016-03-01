"""
newsview.py

Contains administrative views for working with news posts.
"""
from admin_helpers import *

from flask.ext.admin.contrib.sqla import ModelView
from remedy.rad.models import News
from remedy.rad.cktextarea import CKTextAreaField


class NewsView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with news posts.
    """
    can_view_details = True

    # Allow exporting
    can_export = True
    export_max_rows = 0
    column_export_list = (
        'subject',
        'author',
        'summary',
        'body',
        'visible',
        'date_created',
        'id'
    )
    column_formatters_export = news_export_formatters

    column_list = (
        'subject',
        'author',
        'summary',
        'visible',
        'date_created'
    )

    column_default_sort = 'date_created'

    column_sortable_list = (
        'subject',
        'author',
        'summary',
        'visible',
        'date_created'
    )

    column_searchable_list = ('subject', 'author', 'summary', 'body',)

    column_filters = ('visible',)

    form_overrides = dict(body=CKTextAreaField)

    # Use standard labels/descriptions/formatters
    column_labels = news_column_labels
    column_descriptions = news_column_descriptions
    column_formatters = news_column_formatters

    form_excluded_columns = (
        'date_created'
    )

    create_template = 'admin/news_create.html'
    edit_template = 'admin/news_edit.html'

    def __init__(self, session, **kwargs):
        super(NewsView, self).__init__(News, session, **kwargs)
