from admin_helpers import *

from flask.ext.admin.contrib.sqla import ModelView
from remedy.rad.models import News
from remedy.rad.cktextarea import CKTextAreaField


class NewsView(AdminAuthMixin, ModelView):

    can_view_details = True

    form_overrides = dict(text=CKTextAreaField)

    create_template = 'admin/news_create.html'
    edit_template = 'admin/news_edit.html'

    form_excluded_columns = (
        'date_created'
    )

    column_exclude_list = ()

    def __init__(self, session, **kwargs):
        super(NewsView, self).__init__(News, session, **kwargs)
