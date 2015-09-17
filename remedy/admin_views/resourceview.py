"""
resourceview.py

Contains administrative views for working with resources.
"""
from datetime import date

from admin_helpers import *

from sqlalchemy import or_, not_, func

from flask import current_app, redirect, flash, request, url_for
from flask.ext.admin import BaseView, expose
from flask.ext.admin.helpers import get_redirect_target
from flask.ext.admin.actions import action
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.contrib.sqla.filters import FilterEmpty
from wtforms import DecimalField, validators

import geopy
from geopy.exc import *

from remedy.remedyblueprint import group_active_populations, group_active_categories
from remedy.rad.models import Resource, Category
from remedy.rad.geocoder import Geocoder
from remedy.rad.nullablebooleanfield import NullableBooleanField


class ResourceView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with resources.
    """
    can_view_details = True

    column_details_exclude_list = ('latitude', 'longitude', 
        'location', 'category_text')

    # Allow exporting
    can_export = True
    export_max_rows = 0
    column_export_list = ('id', 'name', 'organization', 'address',
        'url', 'email', 'phone', 'fax', 'hours', 'hospital_affiliation',
        'description', 'npi', 'categories', 'populations',
        'is_icath', 'is_wpath', 'is_accessible', 'has_sliding_scale', 'visible',
        'is_approved', 'submitted_user', 'submitted_date', 'submitted_ip',
        'source', 'notes', 'date_created', 'last_updated', 'date_verified')

    column_list = ('name', 'organization', 
        'address', 'url', 
        'source', 'last_updated')

    column_default_sort = 'name'

    column_searchable_list = ('name','description','organization','notes',)

    # By default, Flask-Admin isn't going to pick up on the fact
    # that our flags are nullable. Therefore, we need to manually
    # add FilterEmpty options. These use names identical to the
    # column labels for the normal filters so that they are appropriately grouped.
    column_filters = ('visible', 'source', 'npi', 'date_verified',
        FilterEmpty(Resource.is_icath, 'Informed Consent/ICATH'), 'is_icath', 
        FilterEmpty(Resource.is_wpath, 'WPATH'), 'is_wpath', 
        FilterEmpty(Resource.is_accessible, 'ADA/Wheelchair Accessible'), 'is_accessible', 
        FilterEmpty(Resource.has_sliding_scale, 'Sliding Scale'), 'has_sliding_scale',
    )

    form_excluded_columns = ('date_created', 'last_updated', 
        'category_text', 'reviews', 'aggregateratings', 'submitted_user', 'submitted_ip',
        'submitted_date', 'is_approved')

    create_template = 'admin/resource_create.html'

    edit_template = 'admin/resource_edit.html'

    column_labels = {
        'id': 'ID',
        'npi': 'NPI',
        'url': 'URL',
        'is_icath': 'Informed Consent/ICATH',
        'is_wpath': 'WPATH',
        'is_accessible': 'ADA/Wheelchair Accessible',
        'has_sliding_scale': 'Sliding Scale',
        'submitted_ip': 'Submitted IP',
        'notes': 'Admin Notes'
    }

    column_descriptions = {
        'npi': 'The National Provider Identifier (NPI) of the resource.',
        'hours': 'The hours of operation for the resource.',
        'source': 'The source of the resource\'s information.',
        'notes': 'Administrative notes for the resource, not visible to end users.',
        'date_verified': 'The date the resource was last verified by an administrator.'
    }

    def scaffold_form(self):
        """
        Scaffolds the creation/editing form so that the latitude
        and longitude fields are optional, but can still be set
        by the Google Places API integration.
        """
        form_class = super(ResourceView, self).scaffold_form()

        # Override the latitude/longitude fields to be optional
        form_class.latitude = DecimalField(validators=[validators.Optional()])
        form_class.longitude = DecimalField(validators=[validators.Optional()])

        # Override the nullable flag fields to actually be nullable -
        # otherwise, Flask-Admin treats them as standard Boolean fields
        # (which is bad - we want the N/A option)
        form_class.is_wpath = NullableBooleanField(
            label=self.column_labels['is_wpath'])
        form_class.is_icath = NullableBooleanField(
            label=self.column_labels['is_icath'])
        form_class.is_accessible = NullableBooleanField(
            label=self.column_labels['is_accessible'])
        form_class.has_sliding_scale = NullableBooleanField(
            label=self.column_labels['has_sliding_scale'])

        return form_class

    @action('togglevisible', 
        'Toggle Visibility', 
        'Are you sure you wish to toggle visibility for the selected resources?')
    def action_togglevisible(self, ids):
        """
        Attempts to toggle visibility for each of the specified resources.

        Args:
            ids: The list of resource IDs, indicating which resources
                should have their visibility toggled.
        """
        # Load all resources by the set of IDs
        target_resources = self.get_query().filter(self.model.id.in_(ids)).all()

        # Build a list of all the results
        results = []

        if len(target_resources) > 0:

            for resource in target_resources:
                # Build a helpful message string to use for messages.
                resource_str =  'resource #' + str(resource.id) + ' (' + resource.name + ')'
                visible_status = ''
                try:
                    if not resource.visible:
                        resource.visible = True
                        visible_status = ' as visible'
                    else:
                        resource.visible = False
                        visible_status = ' as not visible'
                except Exception as ex:
                    results.append('Error changing ' + resource_str + ': ' + str(ex))
                else:
                    results.append('Marked ' + resource_str + visible_status + '.')

            # Save our changes.
            self.session.commit()

        else:
            results.append('No resources were selected.')

        # Flash the results of everything
        flash("\n".join(msg for msg in results))

    @action('markverified', 
        'Mark Verified', 
        'Are you sure you wish to mark the selected resources as verified?')
    def action_markverified(self, ids):
        """
        Attempts to mark each of the specified resources as verified
        on the current date.

        Args:
            ids: The list of resource IDs, indicating which resources
                should be marked as verified.
        """
        # Load all resources by the set of IDs
        target_resources = self.get_query().filter(self.model.id.in_(ids)).all()

        # Build a list of all the results
        results = []

        if len(target_resources) > 0:

            for resource in target_resources:
                # Build a helpful message string to use for messages.
                resource_str =  'resource #' + str(resource.id) + ' (' + resource.name + ')'
                try:
                    resource.date_verified = date.today()
                except Exception as ex:
                    results.append('Error changing ' + resource_str + ': ' + str(ex))
                else:
                    results.append('Marked ' + resource_str + ' as verified.')

            # Save our changes.
            self.session.commit()

        else:
            results.append('No resources were selected.')

        # Flash the results of everything
        flash("\n".join(msg for msg in results))

    @action('assigncategories', 'Assign Categories')
    def action_assigncategories(self, ids):
        """
        Sets up a redirection action for mass-assigning categories
        to the specified resources.

        Args:
            ids: The list of resource IDs that should be updated.
        """
        return_url = get_redirect_target() or self.get_url('.index_view')

        return redirect(self.get_url('resourcecategoryassignview.index', 
            url=return_url, ids=ids))

    def __init__(self, session, **kwargs):
        super(ResourceView, self).__init__(Resource, session, **kwargs)


class ResourceRequiringGeocodingView(ResourceView):
    """
    An administrative view for working with resources that need geocoding.
    """
    column_list = ('name', 'organization', 'address', 'source')

    # Disable model creation/deletion
    can_create = False
    can_delete = False

    def get_query(self):
        """
        Returns the query for the model type.

        Returns:
            The query for the model type.
        """
        query = self.session.query(self.model)
        return self.prepare_geocode_query(query)

    def get_count_query(self):
        """
        Returns the count query for the model type.

        Returns:
            The count query for the model type.
        """
        query = self.session.query(func.count('*')).select_from(self.model)
        return self.prepare_geocode_query(query)

    def prepare_geocode_query(self, query):
        """
        Prepares the provided query by ensuring that
        all relevant geocoding-related filters have been applied.

        Args:
            query: The query to update.

        Returns:
            The updated query.
        """
        # Ensure an address is defined
        query = query.filter(self.model.address != None)
        query = query.filter(self.model.address != '')

        # Ensure at least one geocoding field is missing
        query = query.filter(or_(self.model.latitude == None,
            self.model.longitude == None))

        return query

    @action('geocode', 
        'Geocode')
    def action_geocode(self, ids):
        """
        Attempts to geocode each of the specified resources.

        Args:
            ids: The list of resource IDs, indicating which resources
                should be geocoded.
        """
        # Load all resources by the set of IDs
        target_resources = self.get_query().filter(self.model.id.in_(ids)).all()

        # Build a list of all the results
        results = []

        if len(target_resources) > 0:

            # Set up the geocoder, and then try to geocode each resource
            geocoder = Geocoder(api_key=current_app.config.get('MAPS_SERVER_KEY'))

            for resource in target_resources:
                # Build a helpful message string to use for errors.
                resource_str =  'resource #' + str(resource.id) + ' (' + resource.name + ')'
                try:
                    geocoder.geocode(resource)
                except geopy.exc.GeopyError as gpex:                
                    # Handle Geopy errors separately
                    exc_type = ''

                    # Attempt to infer some extra information based on the exception type
                    if isinstance(gpex, geopy.exc.GeocoderQuotaExceeded):
                        exc_type = 'quota exceeded'
                    elif isinstance(gpex, geopy.exc.GeocoderAuthenticationFailure):
                        exc_type = 'authentication failure'
                    elif isinstance(gpex, geopy.exc.GeocoderInsufficientPrivileges):
                        exc_type = 'insufficient privileges'
                    elif isinstance(gpex, geopy.exc.GeocoderUnavailable):
                        exc_type = 'server unavailable'
                    elif isinstance(gpex, geopy.exc.GeocoderTimedOut):
                        exc_type = 'timed out'
                    elif isinstance(gpex, geopy.exc.GeocoderQueryError):
                        exc_type = 'query error'

                    if len(exc_type) > 0:
                        exc_type = '(' + exc_type + ') '

                    results.append('Error geocoding ' + resource_str + ': ' + exc_type + str(gpex))                                        
                except Exception as ex:
                    results.append('Error geocoding ' + resource_str + ': ' + str(ex))
                else:
                    results.append('Geocoded ' + resource_str + '.')

            # Save our changes.
            self.session.commit()

        else:
            results.append('No resources were selected.')

        # Flash the results of everything
        flash("\n".join(msg for msg in results))

    @action('removeaddress', 
        'Remove Address', 
        'Are you sure you wish to remove address information from the selected resources?')
    def action_remove_address(self, ids):
        """
        Attempts to remove address information from each of the specified resources.

        Args:
            ids: The list of resource IDs, indicating which resources
                should have address information stripped.
        """
        # Load all resources by the set of IDs
        target_resources = self.get_query().filter(self.model.id.in_(ids)).all()

        # Build a list of all the results
        results = []

        if len(target_resources) > 0:
            for resource in target_resources:
                # Build a helpful message string to use for errors.
                resource_str =  'resource #' + str(resource.id) + ' (' + resource.name + ')'
                try:
                    resource.address = None
                    resource.latitude = None
                    resource.longitude = None
                    resource.location = None
                except Exception as ex:
                    results.append('Error updating ' + resource_str + ': ' + str(ex))
                else:
                    results.append('Removed address information from ' + resource_str + '.')

            # Save our changes.
            self.session.commit()
        else:
            results.append('No resources were selected.')

        # Flash the results of everything
        flash("\n".join(msg for msg in results))

    def __init__(self, session, **kwargs):
        # Because we're invoking the ResourceView constructor,
        # we don't need to pass in the ResourceModel.
        super(ResourceRequiringGeocodingView, self).__init__(session, **kwargs)


class ResourceRequiringCategoriesView(ResourceView):
    """
    An administrative view for working with resources that need categories.
    """
    column_list = ('name', 'organization', 'address', 'source')

    # Disable model creation/deletion
    can_create = False
    can_delete = False

    def get_query(self):
        """
        Returns the query for the model type.

        Returns:
            The query for the model type.
        """
        query = self.session.query(self.model)
        return self.prepare_category_query(query)

    def get_count_query(self):
        """
        Returns the count query for the model type.

        Returns:
            The count query for the model type.
        """
        query = self.session.query(func.count('*')).select_from(self.model)
        return self.prepare_category_query(query)

    def prepare_category_query(self, query):
        """
        Prepares the provided query by ensuring that
        filtering out resources with categories has been applied.

        Args:
            query: The query to update.

        Returns:
            The updated query.
        """
        # Ensure there are no categories defined
        query = query.filter(not_(self.model.categories.any()))

        return query

    def __init__(self, session, **kwargs):
        # Because we're invoking the ResourceView constructor,
        # we don't need to pass in the ResourceModel.
        super(ResourceRequiringCategoriesView, self).__init__(session, **kwargs)


class ResourceRequiringPopulationsView(ResourceView):
    """
    An administrative view for working with resources that need populations.
    """
    column_list = ('name', 'organization', 'address', 'source')

    # Disable model creation/deletion
    can_create = False
    can_delete = False

    def get_query(self):
        """
        Returns the query for the model type.

        Returns:
            The query for the model type.
        """
        query = self.session.query(self.model)
        return self.prepare_population_query(query)

    def get_count_query(self):
        """
        Returns the count query for the model type.

        Returns:
            The count query for the model type.
        """
        query = self.session.query(func.count('*')).select_from(self.model)
        return self.prepare_population_query(query)

    def prepare_population_query(self, query):
        """
        Prepares the provided query by ensuring that
        filtering out resources with populations has been applied.

        Args:
            query: The query to update.

        Returns:
            The updated query.
        """
        # Ensure there are no populations defined
        query = query.filter(not_(self.model.populations.any()))

        return query

    def __init__(self, session, **kwargs):
        # Because we're invoking the ResourceView constructor,
        # we don't need to pass in the ResourceModel.
        super(ResourceRequiringPopulationsView, self).__init__(session, **kwargs)


class ResourceCategoryAssignView(AdminAuthMixin, BaseView):
    """
    The view for mass-assigning resources to categories.
    """
    # Not visible in the menu.
    def is_visible(self):
        return False

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """
        A view for mass-assigning resources to categories.
        """
        return_url = get_redirect_target() or self.get_url('category-resourceview.index_view')

        # Load all resources by the set of IDs
        target_resources = Resource.query.filter(Resource.id.in_(request.args.getlist('ids')))
        target_resources = target_resources.order_by(Resource.name.asc()).all()

        # Make sure we have some, and go back to the resources
        # view (for assigning categories) if we don't.
        if len(target_resources) == 0:
            flash('At least one resource must be selected.')
            return redirect(url_for(return_url))
        
        if request.method == 'GET':
            # Get all categories
            available_categories = Category.query.order_by(Category.name.asc()).all()

            # Group them using the remedyblueprint method
            grouped_categories = group_active_categories(available_categories)

            # Return the view for assigning categories
            return self.render('admin/resource_assign_categories.html',
                ids = request.args.getlist('ids'),
                resources = target_resources,
                grouped_categories = grouped_categories,
                return_url = return_url)
        else:
            # Get the selected categories - use request.form,
            # not request.args
            target_categories = Category.query.filter(Category.id.in_(request.form.getlist('categories'))).all()

            if len(target_categories) > 0:
                # Build a list of all the results
                results = []

                for resource in target_resources:
                    # Build a helpful message string to use for resources.
                    resource_str =  'resource #' + str(resource.id) + ' (' + resource.name + ')'

                    try:
                        # Assign all categories
                        for category in target_categories:

                            # Make sure we're not double-adding
                            if not category in resource.categories:
                                resource.categories.append(category)

                    except Exception as ex:
                        results.append('Error updating ' + resource_str + ': ' + str(ex))
                    else:
                        results.append('Updated ' + resource_str + '.')

                # Save our changes.
                self.session.commit()

                # Flash the results of everything
                flash("\n".join(msg for msg in results))                
            else:
                flash('At least one category must be selected.')

            return redirect(return_url)

    def __init__(self, session, **kwargs):
        self.session = session
        super(ResourceCategoryAssignView, self).__init__(**kwargs) 


class ResourceRequiringNpiView(ResourceView):
    """
    An administrative view for working with resources that need NPI values.
    """
    # Disable model creation/deletion
    can_create = False
    can_delete = False

    def get_query(self):
        """
        Returns the query for the model type.

        Returns:
            The query for the model type.
        """
        query = self.session.query(self.model)
        return self.prepare_npi_query(query)

    def get_count_query(self):
        """
        Returns the count query for the model type.

        Returns:
            The count query for the model type.
        """
        query = self.session.query(func.count('*')).select_from(self.model)
        return self.prepare_npi_query(query)

    def prepare_npi_query(self, query):
        """
        Prepares the provided query by ensuring that
        filtering out resources with NPIs has been applied.

        Args:
            query: The query to update.

        Returns:
            The updated query.
        """
        # Ensure that an NPI is missing
        query = query.filter(or_(self.model.npi == None,
            self.model.npi == ''))

        return query

    def __init__(self, session, **kwargs):
        # Because we're invoking the ResourceView constructor,
        # we don't need to pass in the ResourceModel.
        super(ResourceRequiringNpiView, self).__init__(session, **kwargs)

