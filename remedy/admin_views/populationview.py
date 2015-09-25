"""
populationview.py

Contains administrative views for working with populations.
"""
from admin_helpers import *

from flask import redirect, flash, request, url_for
from flask.ext.admin import BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.actions import action

from remedy.rad.models import Population, PopulationGroup


class PopulationView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with populations.
    """
    can_view_details = True

    # Allow exporting
    can_export = True
    export_max_rows = 0
    column_export_list = ('grouping', 'name',
        'description', 'keywords',
        'visible', 'date_created', 'id')
    column_formatters_export = catpop_export_formatters
 
    column_list = ('grouping', 'name', 'description', 
        'visible', 'date_created')

    column_default_sort = 'name'

    column_sortable_list = ('name', 'description', 'visible', 'date_created',
        ('grouping', 'grouping.name'))

    column_searchable_list = ('name', 'description',)

    column_filters = ('visible',)

    # Use standard labels/descriptions/formatters
    column_labels = catpop_column_labels
    column_descriptions = catpop_column_descriptions
    column_formatters = catpop_column_formatters

    form_excluded_columns = ('resources', 'users', 'date_created')

    @action('togglevisible', 
        'Toggle Visibility', 
        'Are you sure you wish to toggle visibility for the selected populations?')
    def action_togglevisible(self, ids):
        """
        Attempts to toggle visibility for each of the specified populations.

        Args:
            ids: The list of population IDs, indicating which populations
                should have their visibility toggled.
        """
        # Load all populations by the set of IDs
        target_populations = self.get_query().filter(self.model.id.in_(ids)).all()

        # Build a list of all the results
        results = []

        if len(target_populations) > 0:

            for population in target_populations:
                # Build a helpful message string to use for messages.
                population_str =  'population #' + str(population.id) + ' (' + population.name + ')'
                visible_status = ''
                try:
                    if not population.visible:
                        population.visible = True
                        visible_status = ' as visible'
                    else:
                        population.visible = False
                        visible_status = ' as not visible'
                except Exception as ex:
                    results.append('Error changing ' + population_str + ': ' + str(ex))
                else:
                    results.append('Marked ' + population_str + visible_status + '.')

            # Save our changes.
            self.session.commit()

        else:
            results.append('No populations were selected.')

        # Flash the results of everything
        flash("\n".join(msg for msg in results))

    def __init__(self, session, **kwargs):
        super(PopulationView, self).__init__(Population, session, **kwargs)    

