"""
admin.py

Contains functionality for providing administrative interfaces
to items in the system.
"""
from flask import redirect, flash, request, url_for
from flask.ext.login import current_user
from flask.ext.admin import Admin, AdminIndexView, BaseView, expose
from flask.ext.admin.menu import MenuLink
from flask.ext.admin.actions import action
from flask.ext.admin.contrib.sqla import ModelView
from sqlalchemy import or_, not_, func

from flask_wtf import Form
from wtforms import TextField, StringField, IntegerField, DecimalField, PasswordField, validators, ValidationError

import bcrypt

import rad.reviewservice
from remedy.rad.models import Resource, User, Category, Review, db
from remedy.rad.geocoder import Geocoder

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

class ResourceView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with resources.
    """
    column_list = ('name', 'organization', 
        'address', 'url', 
        'source', 'last_updated')

    column_default_sort = 'name'

    column_searchable_list = ('name','description','organization',)

    column_filters = ('visible','source',)

    form_excluded_columns = ('date_created', 'last_updated', 
        'category_text', 'reviews')

    create_template = 'admin/resource_create.html'

    edit_template = 'admin/resource_edit.html'

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

    @action('assigncategories', 'Assign Categories')
    def action_assigncategories(self, ids):
        """
        Sets up a redirection action for mass-assigning categories
        to the specified resources.

        Args:
            ids: The list of resource IDs that should be updated.
        """
        return redirect(url_for('resourcecategoryassignview.index', ids=ids))

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
            geocoder = Geocoder()

            for resource in target_resources:
                # Build a helpful message string to use for errors.
                resource_str =  'resource #' + str(resource.id) + ' (' + resource.name + ')'
                try:
                    geocoder.geocode(resource)
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
        # Ensure an address is defined
        query = query.filter(not_(self.model.categories.any()))

        return query

    def __init__(self, session, **kwargs):
        # Because we're invoking the ResourceView constructor,
        # we don't need to pass in the ResourceModel.
        super(ResourceRequiringCategoriesView, self).__init__(session, **kwargs)


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
        # Load all resources by the set of IDs
        target_resources = Resource.query.filter(Resource.id.in_(request.args.getlist('ids')))
        target_resources = target_resources.order_by(Resource.name.asc()).all()

        # Make sure we have some, and go back to the resources
        # view (for assigning categories) if we don't.
        if len(target_resources) == 0:
            flash('At least one resource must be selected.')
            return redirect(url_for('category-resourceview.index_view'))
        
        if request.method == 'GET':
            # Get all categories
            available_categories = Category.query.order_by(Category.name.asc())
            available_categories = available_categories.all()

            # Return the view for assigning categories
            return self.render('admin/resource_assign_categories.html',
                ids = request.args.getlist('ids'),
                resources = target_resources,
                categories = available_categories)
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

            return redirect(url_for('category-resourceview.index_view'))

    def __init__(self, session, **kwargs):
        self.session = session
        super(ResourceCategoryAssignView, self).__init__(**kwargs) 


class UserView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with users.
    """
    column_list = ('username', 'email', 
        'admin', 'active', 'date_created')

    column_default_sort = 'username'

    column_searchable_list = ('username', 'email',)

    column_filters = ('admin', 'active',)

    form_excluded_columns = ('password', 'date_created', 'reviews')

    create_template = 'admin/user_create.html'

    edit_template = 'admin/user_edit.html'

    def scaffold_form(self):
        """
        Sets up the user form to ensure that password fields
        are present and that the default latitude/longitude
        fields are treated as optional.
        """
        form_class = super(UserView, self).scaffold_form()

        form_class.username = StringField('Username', validators=[
            validators.DataRequired(), 
            validators.Length(1, message='Username has to be at least 1 character'),
            validators.Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Username must have only letters, numbers, dots or underscores')
        ])

        form_class.email = StringField('Email', validators=[
            validators.DataRequired(), 
            validators.Email(), 
            validators.Length(1, 70)
        ])

        form_class.new_password = PasswordField('New Password', validators=[
            validators.EqualTo('new_password_confirm', message='New passwords must match')
        ])

        form_class.new_password_confirm = PasswordField('Confirm New Password')

        # Override the latitude/longitude fields to be optional
        form_class.default_latitude = DecimalField(validators=[validators.Optional()])
        form_class.default_longitude = DecimalField(validators=[validators.Optional()])

        return form_class

    def update_model(self, form, model):
        """
        Handles when a model is being updated to ensure that
        any password changes are properly handled.

        Args:
            form: The source form.
            model: The model being updated.
        """        
        try:
            form.populate_obj(model)

            # Are we specifying a new password?
            if len(model.new_password):
                newpass = model.new_password
                newpassconfirm = model.new_password_confirm

                # Make sure the passwords match
                if newpass == newpassconfirm:
                    if len(newpass) < 8:
                        raise ValueError('Password must be longer than 8 letters.')
                    else:
                        model.password = bcrypt.hashpw(newpass, bcrypt.gensalt())
                else:
                    raise ValueError('Passwords must match.')

            self.session.commit()
            return True
        except Exception, ex:
            flash('Failed to edit user. ' + str(ex))
            return False

    def create_model(self, form):
        """
        Handles when a model has been created, to ensure that
        a password has been provided and that it has been properly
        hashed.

        Args:
            form: The source form.
        """
        try:
            model = self.model()
            form.populate_obj(model)

            # Require a password if this is a new record.
            if len(model.new_password):
                newpass = model.new_password
                newpassconfirm = model.new_password_confirm

                # Make sure the passwords match
                if len(newpass) and newpass == newpassconfirm:
                    model.password = bcrypt.hashpw(newpass, bcrypt.gensalt())
                elif newpass != newpassconfirm:
                    raise ValueError('Passwords must match.')
            else:
                raise ValueError('A password is required for new users.')

            self.session.add(model)
            self.session.flush()

            self.session.commit()
            return True
        except Exception, ex:
            flash('Failed to create user. ' + str(ex))
            return False

    @action('toggleactive', 
        'Toggle Active', 
        'Are you sure you wish to toggle active status for the selected users?')
    def action_toggleactive(self, ids):
        """
        Attempts to toggle active status for each of the specified users.

        Args:
            ids: The list of user IDs, indicating which users
                should have their active status toggled.
        """
        # Load all users by the set of IDs
        target_users = self.get_query().filter(self.model.id.in_(ids)).all()

        # Build a list of all the results
        results = []

        if len(target_users) > 0:

            for user in target_users:
                # Build a helpful message string to use for messages.
                user_str =  'user #' + str(user.id) + ' (' + user.username + ')'
                active_status = ''
                try:
                    if not user.active:
                        user.active = True
                        active_status = ' as active'
                    else:
                        user.active = False
                        active_status = ' as inactive'
                except Exception as ex:
                    results.append('Error changing ' + user_str + ': ' + str(ex))
                else:
                    results.append('Marked ' + user_str + active_status + '.')

            # Save our changes.
            self.session.commit()

        else:
            results.append('No users were selected.')

        # Flash the results of everything
        flash("\n".join(msg for msg in results))

    def __init__(self, session, **kwargs):
        super(UserView, self).__init__(User, session, **kwargs)    


class CategoryView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with categories.
    """
    column_list = ('name', 'description', 
        'visible', 'date_created')

    column_default_sort = 'name'

    column_searchable_list = ('name', 'description',)

    column_filters = ('visible',)

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

class ReviewView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with resource reviews.
    """
    # Disable model creation
    can_create = False

    column_select_related_list = (Review.resource, Review.user)

    column_default_sort = 'date_created'

    column_list = ('rating', 'resource.name', 'user.username', 'visible', 'date_created')

    column_labels = {
        'rating': 'Rating', 
        'resource.name': 'Resource',
        'user.username': 'User',
        'visible': 'Visible', 
        'date_created': 'Date Created'
    }

    column_searchable_list = ('text',)

    column_filters = ('visible','rating',)

    form_excluded_columns = ('date_created','is_old_review','old_reviews',
        'new_review_id','new_review')

    def scaffold_form(self):
        """
        Sets up the review form to ensure that the rating field
        behaves on a 1-5 scale.
        """
        form_class = super(ReviewView, self).scaffold_form()

        form_class.rating = IntegerField('Rating', validators=[
            validators.DataRequired(), 
            validators.NumberRange(min=1, max=5)
        ])

        return form_class

    def delete_model(self, model):
        """
        Deletes the specified review.

        Args:
            model: The review to delete.
        """
        try:
            rad.reviewservice.delete(self.session, model)
            flash('Review deleted.')
            return True
        except Exception as ex:
            if not super(ReviewView, self).handle_view_exception(ex):
                flash(gettext('Failed to delete model. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to delete model')

            self.session.rollback()

            return False        

    @action('togglevisible', 
        'Toggle Visibility', 
        'Are you sure you wish to toggle visibility for the selected reviews?')
    def action_togglevisible(self, ids):
        """
        Attempts to toggle visibility for each of the specified reviews.

        Args:
            ids: The list of review IDs, indicating which reviews
                should have their visibility toggled.
        """
        # Load all reviews by the set of IDs
        target_reviews = self.get_query().filter(self.model.id.in_(ids)).all()

        # Build a list of all the results
        results = []

        if len(target_reviews) > 0:

            for review in target_reviews:
                # Build a helpful message string to use for messages.
                review_str =  'review #' + str(review.id) + ' (' + review.resource.name + \
                 ' by ' + review.user.username + ')'
                visible_status = ''
                try:
                    if not review.visible:
                        review.visible = True
                        visible_status = ' as visible'
                    else:
                        review.visible = False
                        visible_status = ' as not visible'
                except Exception as ex:
                    results.append('Error changing ' + review_str + ': ' + str(ex))
                else:
                    results.append('Marked ' + review_str + visible_status + '.')

            # Save our changes.
            self.session.commit()

        else:
            results.append('No reviews were selected.')

        # Flash the results of everything
        flash("\n".join(msg for msg in results))

    def __init__(self, session, **kwargs):
        super(ReviewView, self).__init__(Review, session, **kwargs)    

class AdminHomeView(AdminAuthMixin, AdminIndexView):
    """
    The base Admin home view.
    """
    @expose('/')
    def index(self):
        recently_added_count = 5

        newest_resources = Resource.query. \
            order_by(Resource.date_created.desc()). \
            limit(recently_added_count).all()

        newest_reviews = Review.query. \
            order_by(Review.date_created.desc()). \
            limit(recently_added_count).all()

        newest_categories = Category.query. \
            order_by(Category.date_created.desc()). \
            limit(recently_added_count).all()

        newest_users = User.query. \
            order_by(User.date_created.desc()). \
            limit(recently_added_count).all()            

        return self.render('admin/radindex.html', 
            newest_resources = newest_resources,
            newest_reviews = newest_reviews,
            newest_categories = newest_categories,
            newest_users = newest_users,
            return_url = '/admin/')

admin = Admin(name='RAD Remedy Admin',
    index_view=AdminHomeView())
admin.add_view(ResourceView(db.session,
    category='Resource',
    name='All',
    endpoint='resourceview',))
admin.add_view(ResourceRequiringGeocodingView(db.session,
    category='Resource',
    name='Needing Geocoding', 
    endpoint='geocode-resourceview'))
admin.add_view(ResourceRequiringCategoriesView(db.session,
    category='Resource',
    name='Needing Categorization', 
    endpoint='category-resourceview'))
admin.add_view(ResourceCategoryAssignView(db.session))
admin.add_view(UserView(db.session))
admin.add_view(CategoryView(db.session))
admin.add_view(CategoryMergeView(db.session))
admin.add_view(ReviewView(db.session))

# Add a link back to the main site
admin.add_link(MenuLink(name="Main Site", url='/'))
