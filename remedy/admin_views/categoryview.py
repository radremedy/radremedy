"""
categoryview.py

Contains administrative views for working with categories.
"""
from admin_helpers import *

from flask import redirect, flash, request, url_for
from flask.ext.admin import BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.actions import action

from remedy.rad.models import Category


class CategoryView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with categories.
    """
    can_view_details = True
 
    # Allow exporting
    can_export = True

    column_list = ('grouping.name', 'name', 'description', 
        'visible', 'date_created')

    column_default_sort = 'name'

    column_searchable_list = ('name', 'description',)

    column_filters = ('visible',)

    column_labels = {
        'grouping.name': 'Group',
        'date_created': 'Date Created'
    }

    column_descriptions = dict(
        keywords='The keywords used to search for the category, separated by spaces or newlines. ' \
        + 'Include synonyms and category specializations.')

    form_excluded_columns = ('resources', 'date_created')

    @action('togglevisible', 
        'Toggle Visibility', 
        'Are you sure you wish to toggle visibility for the selected categories?')
    def action_togglevisible(self, ids):
        """
        Attempts to toggle visibility for each of the specified categories.

        Args:
            ids: The list of category IDs, indicating which categories
                should have their visibility toggled.
        """
        # Load all categories by the set of IDs
        target_categories = self.get_query().filter(self.model.id.in_(ids)).all()

        # Build a list of all the results
        results = []

        if len(target_categories) > 0:

            for category in target_categories:
                # Build a helpful message string to use for messages.
                category_str =  'category #' + str(category.id) + ' (' + category.name + ')'
                visible_status = ''
                try:
                    if not category.visible:
                        category.visible = True
                        visible_status = ' as visible'
                    else:
                        category.visible = False
                        visible_status = ' as not visible'
                except Exception as ex:
                    results.append('Error changing ' + category_str + ': ' + str(ex))
                else:
                    results.append('Marked ' + category_str + visible_status + '.')

            # Save our changes.
            self.session.commit()

        else:
            results.append('No categories were selected.')

        # Flash the results of everything
        flash("\n".join(msg for msg in results))

    @action('merge', 'Merge')
    def action_merge(self, ids):
        """
        Sets up a redirection action for merging the specified
        categories.

        Args:
            ids: The list of category IDs that should be merged.
        """
        return redirect(url_for('categorymergeview.index', ids=ids))

    def __init__(self, session, **kwargs):
        super(CategoryView, self).__init__(Category, session, **kwargs)    


class CategoryMergeView(AdminAuthMixin, BaseView):
    """
    The view for merging categories.
    """
    # Not visible in the menu.
    def is_visible(self):
        return False

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """
        A view for merging categories.
        """
        # Load all categories by the set of IDs
        target_categories = Category.query.filter(Category.id.in_(request.args.getlist('ids')))
        target_categories = target_categories.order_by(Category.name.asc()).all()

        # Make sure we have some, and go back to the categories
        # view if we don't.
        if len(target_categories) <= 1:
            flash('More than one category must be selected.')
            return redirect(url_for('categoryview.index_view'))
        
        if request.method == 'GET':
            # Return the view for merging categories
            return self.render('admin/category_merge.html',
                ids = request.args.getlist('ids'),
                categories = target_categories)
        else:
            # Find the specified category - use request.form,
            # not request.args
            primary_category = next((c for c in target_categories if c.id == int(request.form.get('category'))), None)

            if primary_category is not None:
                # Build a list of all the results
                results = []

                results.append('Primary category: ' + primary_category.name + ' (#' + str(primary_category.id) + ').')

                for category in target_categories:
                    # Skip over the primary category.
                    if category.id == primary_category.id:
                        continue

                    # Build a helpful message string to use for messages.
                    category_str =  'category #' + str(category.id) + ' (' + category.name + ')'
                    try:
                        # Delegate all resources
                        for resource in category.resources:

                            # Make sure we're not double-adding
                            if not resource in primary_category.resources:
                                primary_category.resources.append(resource)

                        # Delete the category
                        self.session.delete(category)

                    except Exception as ex:
                        results.append('Error merging ' + category_str + ': ' + str(ex))
                    else:
                        results.append('Merged ' + category_str + '.')

                # Save our changes.
                self.session.commit()

                # Flash the results of everything
                flash("\n".join(msg for msg in results))                
            else:
                flash('The selected category was not found.')

            return redirect(url_for('categoryview.index_view'))

    def __init__(self, session, **kwargs):
        self.session = session
        super(CategoryMergeView, self).__init__(**kwargs) 
