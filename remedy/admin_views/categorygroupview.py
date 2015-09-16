"""
categorygroupview.py

Contains administrative views for working with category groups.
"""
from admin_helpers import *

from flask import redirect, flash, request, url_for
from flask.ext.admin import BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.actions import action

from remedy.rad.models import Category, CategoryGroup


class CategoryGroupView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with category groups.
    """
    can_view_details = True
  
    # Allow exporting
    can_export = True
    export_max_rows = 0

    column_list = ('grouporder', 'name', 'description', 'date_created')

    column_default_sort = 'grouporder'

    column_searchable_list = ('name', 'description',)

    column_labels = {
        'grouporder': 'Order', 
        'date_created': 'Date Created'
    }

    form_excluded_columns = ('categories','date_created')

    def __init__(self, session, **kwargs):
        super(CategoryGroupView, self).__init__(CategoryGroup, session, **kwargs)    

