"""
reviewview.py

Contains administrative views for working with reviews.
"""
from admin_helpers import *

from flask import flash
from flask.ext.admin.actions import action
from flask.ext.admin.contrib.sqla import ModelView
from wtforms import IntegerField, validators

import remedy.rad.reviewservice
from remedy.rad.models import Review


class ReviewView(AdminAuthMixin, ModelView):
    """
    An administrative view for working with resource reviews.
    """
    # Allow details
    can_view_details = True

    column_details_exclude_list = (
        'is_old_review',
        'new_review_id',
        'new_review'
    )

    # Allow exporting
    can_export = True
    export_max_rows = 0
    column_export_list = (
        'resource',
        'user',
        'rating',
        'staff_rating',
        'intake_rating',
        'text',
        'visible',
        'ip',
        'date_created',
        'id'
    )
    column_formatters_export = review_export_formatters

    # Disable model creation
    can_create = False

    column_default_sort = (Review.date_created, True)

    column_list = (
        'composite_rating',
        'resource',
        'user',
        'visible',
        'date_created'
    )

    column_sortable_list = (
        'composite_rating',
        'visible',
        'date_created',
        ('resource', 'resource.name'),
        ('user', 'user.username')
    )

    # Use the default column labels/descriptions/formatters
    column_labels = review_column_labels
    column_descriptions = review_column_descriptions
    column_formatters = review_column_formatters

    column_searchable_list = ('text',)

    column_filters = (
        'visible',
        'composite_rating',
        'rating',
        'staff_rating',
        'intake_rating',
        'ip'
    )

    form_excluded_columns = (
        'date_created',
        'is_old_review',
        'old_reviews',
        'new_review_id',
        'new_review',
        'composite_rating',
        'ip',
        'user_id',
        'user',
        'resource_id',
        'resource'
    )

    def scaffold_form(self):
        """
        Sets up the review form to ensure that the rating field
        behaves on a 1-5 scale.
        """
        form_class = super(ReviewView, self).scaffold_form()

        form_class.rating = IntegerField(
            review_column_labels['rating'],
            validators=[
                validators.Required(),
                validators.NumberRange(min=1, max=5)
            ]
        )

        form_class.staff_rating = IntegerField(
            review_column_labels['staff_rating'],
            validators=[
                validators.Optional(),
                validators.NumberRange(min=1, max=5)
            ]
        )

        form_class.intake_rating = IntegerField(
            review_column_labels['intake_rating'],
            validators=[
                validators.Optional(),
                validators.NumberRange(min=1, max=5)
            ]
        )

        return form_class

    def delete_model(self, model):
        """
        Deletes the specified review.

        Args:
            model: The review to delete.
        """
        try:
            remedy.rad.reviewservice.delete(self.session, model)
            flash('Review deleted.', 'success')
            return True
        except Exception as ex:
            if not super(ReviewView, self).handle_view_exception(ex):
                flash(
                    gettext(
                        'Failed to delete model. %(error)s', error=str(ex)),
                    'error')
                log.exception('Failed to delete model')

            self.session.rollback()

            return False

    @action(
        'togglevisible',
        'Toggle Visibility',
        'Are you sure you wish to toggle visibility ' +
        'for the selected reviews?')
    def action_togglevisible(self, ids):
        """
        Attempts to toggle visibility for each of the specified reviews.

        Args:
            ids: The list of review IDs, indicating which reviews
                should have their visibility toggled.
        """
        # Load all reviews by the set of IDs
        target_reviews = self.get_query(). \
            filter(self.model.id.in_(ids)).all()

        # Build a list of all the results
        results = []

        if len(target_reviews) > 0:

            for review in target_reviews:
                # Build a helpful string to use for messages.
                review_str = 'review #' + str(review.id) + \
                    ' (' + review.resource.name + \
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
                    results.append(
                        'Error changing ' + review_str + ': ' + str(ex))
                else:
                    results.append(
                        'Marked ' + review_str + visible_status + '.')

            # Save our changes.
            self.session.commit()

        else:
            results.append('No reviews were selected.')

        # Flash the results of everything
        flash("\n".join(msg for msg in results))

    def __init__(self, session, **kwargs):
        super(ReviewView, self).__init__(Review, session, **kwargs)
