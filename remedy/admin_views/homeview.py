"""
homeview.py

Contains the home administrative view.
"""
from admin_helpers import *

from flask.ext.admin import AdminIndexView, expose

from remedy.rad.models import Resource, User, Category, Review


class AdminHomeView(AdminAuthMixin, AdminIndexView):
    """
    The base Admin home view.
    """
    @expose('/')
    def index(self):
        recently_added_count = 5

        newest_resources = Resource.query. \
            filter(Resource.visible == True). \
            filter(Resource.is_approved == True). \
            order_by(Resource.date_created.desc()). \
            limit(recently_added_count).all()

        newest_reviews = Review.query. \
            join(Review.resource). \
            filter(Resource.visible == True). \
            filter(Resource.is_approved == True). \
            filter(Review.visible == True). \
            filter(Review.is_old_review == False). \
            order_by(Review.date_created.desc()). \
            limit(recently_added_count).all()

        newest_categories = Category.query. \
            filter(Category.visible == True). \
            order_by(Category.date_created.desc()). \
            limit(recently_added_count).all()

        newest_users = User.query. \
            order_by(User.date_created.desc()). \
            limit(recently_added_count).all()

        return self.render(
            'admin/radindex.html',
            newest_resources=newest_resources,
            newest_reviews=newest_reviews,
            newest_categories=newest_categories,
            newest_users=newest_users,
            return_url='/admin/')
