"""

reviewservice.py 

This module contains functionality for interacting with review models in
the database.

"""

from sqlalchemy import *
from models import Review

def delete(session, review):
    """
    Deletes a review.

    Args:
        session: The current database session.
        review: The review to delete.
    """
    # See if we have other existing reviews from this user
    # on this resource - order by newest so we can easily
    # get the first visible review
    existing_reviews = Review.query. \
        filter(Review.id != review.id). \
        filter(Review.resource_id == review.resource_id). \
        filter(Review.user_id == review.user_id). \
        order_by(Review.date_created.desc()). \
        all()

    # Find the first visible review
    newest_visible_review = next((rev for rev in existing_reviews if rev.visible == True), None)

    # If we found it, mark it as the top review
    if newest_visible_review is not None:
        newest_visible_review.is_old_review = False
        newest_visible_review.new_review_id = None

    # Now iterate over each existing review
    for existing_review in existing_reviews:

        # See if we have a newest visible review
        if newest_visible_review is not None:

            # Don't touch the newest review
            if existing_review.id == newest_visible_review.id:
                continue

            # Point the existing review to the new one
            existing_review.is_old_review = True
            existing_review.new_review_id = newest_visible_review.id

        else:
            # No new visible review - null out the new review reference
            # in that case, so we don't get FK errors on our delete.
            existing_review.new_review_id = None

    # After all that, delete the review
    session.delete(review)
    session.commit()
