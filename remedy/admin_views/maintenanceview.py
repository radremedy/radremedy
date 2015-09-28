"""
maintenanceview.py

Contains maintenance views for performing dark magic upon data.
"""
from datetime import datetime

from admin_helpers import *

from sqlalchemy import or_, not_, func

from flask import current_app, redirect, flash, request, url_for
from flask.ext.admin import BaseView, expose
from flask.ext.admin.helpers import get_redirect_target

from remedy.remedyblueprint import group_active_populations, \
    group_active_categories
from remedy.rad.models import Resource, Category, Population


class MaintenanceView(AdminAuthMixin, BaseView):
    """
    The view for performing data maintenance.
    """
    # Not visible in the menu.
    def is_visible(self):
        return False

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """
        A view for performing various acts of data maintenance.
        """
        return_url = get_redirect_target() or \
            self.get_url('maintenanceview.index')

        if request.method == 'GET':
            # Get all categories and group them
            # using the remedyblueprint method
            grouped_categories = group_active_categories(
                Category.query.all())

            # Get all populations and group them
            # using the remedyblueprint method
            grouped_populations = group_active_populations(
                Population.query.all())

            return self.render(
                'admin/maintenance.html',
                grouped_populations=grouped_populations,
                grouped_categories=grouped_categories,
                return_url=return_url)
        else:
            query = Resource.query

            # See if there's categories/populations to filter on
            categories = request.form.getlist('categories')
            populations = request.form.getlist('populations')

            if len(categories) > 0:
                query = query.filter(Resource.categories.any(
                    Category.id.in_(categories)))

            if len(populations) > 0:
                query = query.filter(Resource.populations.any(
                    Population.id.in_(populations)))

            # Now apply our filtering.
            target_resources = query.all()

            if len(target_resources) > 0:
                # Touch the last-updated date.
                for resource in target_resources:
                    resource.last_updated = datetime.utcnow()

                # Save our changes.
                self.session.commit()

                # Indicate how many we changed.
                flash(
                    'Updated ' + str(len(target_resources)) + ' resource(s).',
                    'success')
            else:
                flash('No resources matched the provided query.', 'warning')

            return redirect(return_url)

    def __init__(self, session, **kwargs):
        self.session = session
        super(MaintenanceView, self).__init__(**kwargs)
