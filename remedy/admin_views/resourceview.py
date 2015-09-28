"""
resourceview.py

Contains administrative views for working with resources.
"""
from datetime import date, datetime

from admin_helpers import *

from sqlalchemy import or_, not_, and_, func
from flask import current_app, redirect, flash, request, url_for
from flask.ext.admin import BaseView, expose
from flask.ext.admin.form import rules
from flask.ext.admin.helpers import get_redirect_target
from flask.ext.admin.actions import action
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.contrib.sqla.filters import FilterEmpty
from wtforms import DecimalField, validators

import geopy
from geopy.exc import *

from remedy.remedyblueprint import group_active_populations, group_active_categories
from remedy.rad.models import Resource, Category, Population, Review
from remedy.rad.geocoder import Geocoder
from remedy.rad.nullablebooleanfield import NullableBooleanField
from remedy.rad.plaintextfield import PlainTextField
from remedy.rad.statichtmlfield import StaticHtmlField


def scaffold_resource_form(form_class):
    """
    Scaffolds the provided resource form class by ensuring
    location fields are optional and that nullable flag fields
    are actually handled as nullable.

    Args:
        form_class: The form class to update.
        column_labels: The column labels to use.

    Returns:
        The updated form class.
    """
    # Override the latitude/longitude fields to be optional
    form_class.latitude = DecimalField(validators=[validators.Optional()])
    form_class.longitude = DecimalField(validators=[validators.Optional()])

    # Override the nullable flag fields to actually be nullable -
    # otherwise, Flask-Admin treats them as standard Boolean fields
    # (which is bad - we want the N/A option)
    form_class.is_wpath = NullableBooleanField(
        label=resource_column_labels['is_wpath'])
    form_class.is_icath = NullableBooleanField(
        label=resource_column_labels['is_icath'])
    form_class.is_accessible = NullableBooleanField(
        label=resource_column_labels['is_accessible'])
    form_class.has_sliding_scale = NullableBooleanField(
        label=resource_column_labels['has_sliding_scale'])

    return form_class


class ResourceView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with resources.
    """
    can_view_details = True

    column_details_exclude_list = (
        'latitude',
        'longitude',
        'location',
        'category_text'
    )

    # Allow exporting
    can_export = True
    export_max_rows = 0
    column_export_list = (
        'name',
        'organization',
        'address',
        'url',
        'email',
        'phone',
        'fax',
        'hours',
        'hospital_affiliation',
        'description',
        'npi',
        'categories',
        'populations',
        'is_icath',
        'is_wpath',
        'is_accessible',
        'has_sliding_scale',
        'visible',
        'is_approved',
        'submitted_user',
        'submitted_date',
        'submitted_ip',
        'source',
        'notes',
        'date_created',
        'last_updated',
        'date_verified',
        'id'
    )
    column_formatters_export = resource_export_formatters

    column_list = (
        'name',
        'organization',
        'address',
        'url',
        'source',
        'last_updated'
    )

    column_default_sort = 'name'

    column_searchable_list = (
        'name',
        'description',
        'organization',
        'notes',
    )

    # By default, Flask-Admin isn't going to pick up on the fact
    # that our flags are nullable. Therefore, we need to manually
    # add FilterEmpty options. These use names identical to the
    # column labels for the normal filters so that they are appropriately grouped.
    column_filters = (
        'visible',
        'is_approved',
        'source',
        'npi',
        'date_verified',
        FilterEmpty(Resource.is_icath, 'Informed Consent/ICATH'),
        'is_icath',
        FilterEmpty(Resource.is_wpath, 'WPATH'),
        'is_wpath',
        FilterEmpty(Resource.is_accessible, 'ADA/Wheelchair Accessible'),
        'is_accessible',
        FilterEmpty(Resource.has_sliding_scale, 'Sliding Scale'),
        'has_sliding_scale',
    )

    form_excluded_columns = (
        'date_created',
        'last_updated',
        'category_text',
        'reviews',
        'aggregateratings',
        'submitted_user',
        'submitted_ip',
        'submitted_date',
        'is_approved'
    )

    form_rules = [
        rules.FieldSet((
            rules.HTML('<hr />'),
            'name',
            'organization',
            'description',
            'categories',
            'populations',
            'visible',
            rules.HTML('<hr />')),
            'Basic Information'),

        rules.FieldSet((
            rules.HTML('<hr />'),
            'address',
            'latitude',
            'longitude',
            'location',
            'phone',
            'fax',
            'email',
            'url',
            'hours',
            rules.HTML('<hr />')),
            'Contact Information'),

        rules.FieldSet((
            rules.HTML('<hr />'),
            'hospital_affiliation',
            'is_icath',
            'is_wpath',
            'is_accessible',
            'has_sliding_scale',
            rules.HTML('<hr />')),
            'Practice Information'),

        rules.FieldSet((
            rules.HTML('<hr />'),
            'npi',
            'date_verified',
            'notes',
            'source'),
            'Other')
    ]

    create_template = 'admin/resource_create.html'

    edit_template = 'admin/resource_edit.html'

    # Use standard labels/descriptions/formatters
    column_labels = resource_column_labels
    column_descriptions = resource_column_descriptions
    column_formatters = resource_column_formatters

    def edit_form(self, obj=None):
        """
        Overrides the editing form to disable toggling
        active status on unapproved resources.
        """
        form = super(ResourceView, self).edit_form(obj)

        # Disable the "Visible" field if we're attempting to edit
        # an unapproved resource
        if obj is not None and not obj.is_approved:
            del form.visible

        return form

    def scaffold_form(self):
        """
        Scaffolds the creation/editing form so that the latitude
        and longitude fields are optional, but can still be set
        by the Google Places API integration.
        """
        form_class = super(ResourceView, self).scaffold_form()

        # Scaffold our default stuff
        form_class = scaffold_resource_form(form_class)

        return form_class

    def on_model_change(self, form, model, is_created):
        """
        Updates the last_updated date on the provided model
        if is_created is false.
        """
        if not is_created:
            model.last_updated = datetime.utcnow()

    @action(
        'togglevisible',
        'Toggle Visibility',
        'Are you sure you wish to toggle visibility for the selected resources?')
    def action_togglevisible(self, ids):
        """
        Attempts to toggle visibility for each of the specified resources.

        Args:
            ids: The list of resource IDs, indicating which resources
                should have their visibility toggled.
        """
        # Load all resources by the set of IDs - also, only
        # allow this for approved resources
        target_resources = self.get_query(). \
            filter(self.model.id.in_(ids)). \
            filter(self.model.is_approved == True). \
            all()

        # Build a list of all the results
        results = []

        if len(target_resources) > 0:

            for resource in target_resources:
                # Build a helpful message string to use for messages.
                resource_str = 'resource #' + str(resource.id) + ' (' + resource.name + ')'
                visible_status = ''
                try:

                    if not resource.visible:
                        resource.visible = True
                        visible_status = ' as visible'
                    else:
                        resource.visible = False
                        visible_status = ' as not visible'

                    resource.last_updated = datetime.utcnow()
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

    @action(
        'markverified',
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
                resource_str = 'resource #' + str(resource.id) + ' (' + resource.name + ')'
                try:
                    resource.date_verified = date.today()
                    resource.last_updated = datetime.utcnow()
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

        return redirect(
            self.get_url(
                'resourcecategoryassignview.index',
                url=return_url,
                ids=ids))

    @action('assignpopulations', 'Assign Populations')
    def action_assignpopulations(self, ids):
        """
        Sets up a redirection action for mass-assigning populations
        to the specified resources.

        Args:
            ids: The list of resource IDs that should be updated.
        """
        return_url = get_redirect_target() or self.get_url('.index_view')

        return redirect(
            self.get_url(
                'resourcepopulationassignview.index',
                url=return_url,
                ids=ids))

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
        query = query.filter(self.model.address == None)
        query = query.filter(self.model.address != '')

        # Ensure at least one geocoding field is missing
        query = query.filter(or_(
            self.model.latitude == None,
            self.model.longitude == None))

        return query

    @action(
        'geocode',
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
                resource_str = 'resource #' + str(resource.id) + ' (' + resource.name + ')'
                try:
                    geocoder.geocode(resource)
                    resource.last_updated = datetime.utcnow()
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

    @action(
        'removeaddress',
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
                resource_str = 'resource #' + str(resource.id) + ' (' + resource.name + ')'
                try:
                    resource.address = None
                    resource.latitude = None
                    resource.longitude = None
                    resource.location = None
                    resource.last_updated = datetime.utcnow()
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
            flash('At least one resource must be selected.', 'error')
            return redirect(url_for(return_url))

        if request.method == 'GET':
            # Get all categories
            available_categories = Category.query.order_by(Category.name.asc()).all()

            # Group them using the remedyblueprint method
            grouped_categories = group_active_categories(available_categories)

            # Return the view for assigning categories
            return self.render(
                'admin/resource_assign_categories.html',
                ids=request.args.getlist('ids'),
                resources=target_resources,
                grouped_categories=grouped_categories,
                return_url=return_url)
        else:
            # Get the selected categories - use request.form,
            # not request.args
            target_categories = Category.query.filter(Category.id.in_(request.form.getlist('categories'))).all()

            if len(target_categories) > 0:
                # Build a list of all the results
                results = []

                for resource in target_resources:
                    # Build a helpful message string to use for resources.
                    resource_str = 'resource #' + str(resource.id) + ' (' + resource.name + ')'

                    try:
                        # Assign all categories
                        for category in target_categories:

                            # Make sure we're not double-adding
                            if category not in resource.categories:
                                resource.categories.append(category)
                                resource.last_updated = datetime.utcnow()

                    except Exception as ex:
                        results.append('Error updating ' + resource_str + ': ' + str(ex))
                    else:
                        results.append('Updated ' + resource_str + '.')

                # Save our changes.
                self.session.commit()

                # Flash the results of everything
                flash("\n".join(msg for msg in results))
            else:
                flash('At least one category must be selected.', 'error')

            return redirect(return_url)

    def __init__(self, session, **kwargs):
        self.session = session
        super(ResourceCategoryAssignView, self).__init__(**kwargs)


class ResourcePopulationAssignView(AdminAuthMixin, BaseView):
    """
    The view for mass-assigning resources to populations.
    """
    # Not visible in the menu.
    def is_visible(self):
        return False

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """
        A view for mass-assigning resources to populations.
        """
        return_url = get_redirect_target() or self.get_url('population-resourceview.index_view')

        # Load all resources by the set of IDs
        target_resources = Resource.query.filter(Resource.id.in_(request.args.getlist('ids')))
        target_resources = target_resources.order_by(Resource.name.asc()).all()

        # Make sure we have some, and go back to the resources
        # view (for assigning populations) if we don't.
        if len(target_resources) == 0:
            flash('At least one resource must be selected.', 'error')
            return redirect(url_for(return_url))

        if request.method == 'GET':
            # Get all populations
            available_populations = Population.query.order_by(Population.name.asc()).all()

            # Group them using the remedyblueprint method
            grouped_populations = group_active_populations(available_populations)

            # Return the view for assigning populations
            return self.render(
                'admin/resource_assign_populations.html',
                ids=request.args.getlist('ids'),
                resources=target_resources,
                grouped_populations=grouped_populations,
                return_url=return_url)
        else:
            # Get the selected populations - use request.form,
            # not request.args
            target_populations = Population.query.filter(Population.id.in_(request.form.getlist('populations'))).all()

            if len(target_populations) > 0:
                # Build a list of all the results
                results = []

                for resource in target_resources:
                    # Build a helpful message string to use for resources.
                    resource_str = 'resource #' + str(resource.id) + ' (' + resource.name + ')'

                    try:
                        # Assign all populations
                        for population in target_populations:

                            # Make sure we're not double-adding
                            if population not in resource.populations:
                                resource.populations.append(population)
                                resource.last_updated = datetime.utcnow()

                    except Exception as ex:
                        results.append('Error updating ' + resource_str + ': ' + str(ex))
                    else:
                        results.append('Updated ' + resource_str + '.')

                # Save our changes.
                self.session.commit()

                # Flash the results of everything
                flash("\n".join(msg for msg in results))
            else:
                flash('At least one population must be selected.', 'error')

            return redirect(return_url)

    def __init__(self, session, **kwargs):
        self.session = session
        super(ResourcePopulationAssignView, self).__init__(**kwargs)


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
        query = query.filter(or_(
            self.model.npi == None,
            self.model.npi == ''))

        return query

    def __init__(self, session, **kwargs):
        # Because we're invoking the ResourceView constructor,
        # we don't need to pass in the ResourceModel.
        super(ResourceRequiringNpiView, self).__init__(session, **kwargs)


class SubmittedResourceView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with submitted resources
    pending administrator approval.
    """
    can_view_details = True

    column_details_exclude_list = (
        'latitude',
        'longitude',
        'location',
        'category_text',
        'is_approved',
        'visible',
        'date_verified'
    )

    # Disable model creation
    can_create = False

    # Allow exporting
    can_export = True
    export_max_rows = 0
    column_export_list = (
        'name',
        'organization',
        'address',
        'url',
        'email',
        'phone',
        'fax',
        'hours',
        'hospital_affiliation',
        'description',
        'npi',
        'categories',
        'populations',
        'is_icath',
        'is_wpath',
        'is_accessible',
        'has_sliding_scale',
        'submitted_user',
        'submitted_date',
        'submitted_ip',
        'notes',
        'date_created',
        'last_updated',
        'id'
    )
    column_formatters_export = resource_export_formatters

    column_list = (
        'name',
        'organization',
        'address',
        'url',
        'submitted_user',
        'submitted_date'
    )

    column_default_sort = 'submitted_date'

    column_sortable_list = (
        'name',
        'organization',
        'submitted_date',
        'address',
        'url',
        ('submitted_user', 'submitted_user.username')
    )

    column_searchable_list = (
        'name',
        'description',
        'organization',
        'notes',
    )

    column_filters = (
        'submitted_date',
    )

    form_excluded_columns = (
        'date_created',
        'last_updated',
        'category_text',
        'reviews',
        'aggregateratings',
        'submitted_user',
        'submitted_ip',
        'submitted_date',
        'is_approved',
        'visible',
        'source'
    )

    edit_template = 'admin/submitted_resource_edit.html'

    # Use standard labels/descriptions/formatters
    column_labels = resource_column_labels
    column_descriptions = resource_column_descriptions
    column_formatters = resource_column_formatters

    form_extra_fields = {
        'potential_dupes': StaticHtmlField('Detected'),
        'submitted_user_text': StaticHtmlField(resource_column_labels['submitted_user']),
        'submitted_ip_text': PlainTextField(resource_column_labels['submitted_ip']),
        'submitted_date_text': PlainTextField(resource_column_labels['submitted_date']),
        'review_rating': PlainTextField(review_column_labels['rating']),
        'review_staff_rating': PlainTextField(review_column_labels['staff_rating']),
        'review_intake_rating': PlainTextField(review_column_labels['intake_rating']),
        'review_text': PlainTextField(review_column_labels['text'])
    }

    form_rules = [
        rules.FieldSet((
            rules.HTML('<hr />'),
            'potential_dupes',
            rules.HTML('<hr />')),
            'Potential Duplicates'),

        rules.FieldSet((
            rules.HTML('<hr />'),
            'name',
            'organization',
            'description',
            'categories',
            'populations',
            rules.HTML('<hr />')),
            'Basic Information'),

        rules.FieldSet((
            rules.HTML('<hr />'),
            'address',
            'latitude',
            'longitude',
            'location',
            'phone',
            'fax',
            'email',
            'url',
            'hours',
            rules.HTML('<hr />')),
            'Contact Information'),

        rules.FieldSet((
            rules.HTML('<hr />'),
            'hospital_affiliation',
            'is_icath',
            'is_wpath',
            'is_accessible',
            'has_sliding_scale',
            rules.HTML('<hr />')),
            'Practice Information'),

        rules.FieldSet((
            rules.HTML('<hr />'),
            'npi',
            'date_verified',
            'notes',
            rules.HTML('<hr />')),
            'Other'),

        rules.FieldSet((
            rules.HTML('<hr />'),
            'submitted_user_text',
            'submitted_ip_text',
            'submitted_date_text',
            rules.HTML('<hr />')),
            'Submission Information'),

        rules.FieldSet((
            rules.HTML('<hr />'),
            'review_rating',
            'review_staff_rating',
            'review_intake_rating',
            'review_text'),
            'Review')
    ]

    def get_query(self):
        """
        Returns the query for the model type.

        Returns:
            The query for the model type.
        """
        query = self.session.query(self.model)
        return self.prepare_submitted_query(query)

    def get_count_query(self):
        """
        Returns the count query for the model type.

        Returns:
            The count query for the model type.
        """
        query = self.session.query(func.count('*')).select_from(self.model)
        return self.prepare_submitted_query(query)

    def prepare_submitted_query(self, query):
        """
        Prepares the provided query by ensuring that
        only resources pending approval are included.

        Args:
            query: The query to update.

        Returns:
            The updated query.
        """
        # Ensure a submission IP is defined
        query = query.filter(self.model.submitted_ip.isnot(None))
        query = query.filter(self.model.submitted_ip != '')

        # Ensure that we're marked as visible and unapproved
        query = query.filter(self.model.visible == True)
        query = query.filter(self.model.is_approved == False)

        return query

    def edit_form(self, obj=None):
        """
        Overrides the editing form to include additional
        read-only plain text and HTML fields regarding
        the submitted resource.
        """
        form = super(SubmittedResourceView, self).edit_form(obj)

        # Try to detect duplicates based on matching names/NPIs
        dup_resources = self.session.query(Resource). \
            filter(Resource.id != obj.id). \
            filter(or_(
                and_(
                    Resource.npi != '',
                    Resource.npi.isnot(None),
                    Resource.npi == obj.npi),
                Resource.name == obj.name.strip())). \
            all()

        if len(dup_resources) > 0:
            # Build a list of potential duplicates with a link -
            # make sure we're escaping each item.
            form.potential_dupes.default = '<br />'.join(
                [get_resource_link(r) + ' (ID: ' + str(r.id) + ')'
                    for r in dup_resources])
        else:
            form.potential_dupes.default = 'None'

        # Add read-only submission fields
        if obj.submitted_user is not None:
            # Get fancy and have a user link and email
            user_text = get_user_link(obj.submitted_user) + ' - ' + \
                get_email_link(
                    obj.submitted_user,
                    'Provider Submission - ' + obj.name)

            form.submitted_user_text.default = user_text
        else:
            form.submitted_user_text.default = 'Deleted User'

        form.submitted_ip_text.default = obj.submitted_ip
        form.submitted_date_text.default = obj.submitted_date

        # Add review fields
        review = obj.reviews.first()

        if review is not None:
            form.review_text.default = review.text
            form.review_rating.default = review.rating
            form.review_intake_rating.default = review.intake_rating
            form.review_staff_rating.default = review.staff_rating

        return form

    def scaffold_form(self):
        """
        Scaffolds the creation/editing form so that the latitude
        and longitude fields are optional, but can still be set
        by the Google Places API integration.
        """
        form_class = super(SubmittedResourceView, self).scaffold_form()

        # Scaffold our default stuff
        form_class = scaffold_resource_form(form_class)

        return form_class

    def on_model_change(self, form, model, is_created):
        """
        Ensures that fields are updated in response to specific
        approval/rejection actions.

        Also updates the last_updated date on the provided model
        if is_created is false.
        """
        if not is_created:
            model.last_updated = datetime.utcnow()

        # If we're approving, mark the resource as approved
        # and update the verified date.
        # If we're rejecting, mark the resource as hidden.
        if '_approve_resource' in request.form:
            model.is_approved = True
            model.date_verified = date.today()
        elif '_reject_resource' in request.form:
            model.visible = False

    def __init__(self, session, **kwargs):
        super(SubmittedResourceView, self).__init__(Resource, session, **kwargs)
