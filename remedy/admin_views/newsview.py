from admin_helpers import *

from flask import redirect, flash, request, url_for
from flask.ext.admin import BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.actions import action

from remedy.rad.models import News
from wtforms import fields, widgets


class CKTextAreaWidget(widgets.TextArea):
	def __call__(self, field, **kwargs):
		kwargs['class'] = 'form-control ckeditor'
		return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(fields.TextAreaField):
	widget = CKTextAreaWidget()


class NewsView(AdminAuthMixin, ModelView):
	
	##can_view_details = True
	
	form_overrides = dict(text=CKTextAreaField)

	create_template = 'admin/news_create.html'
	edit_template = 'admin/news_edit.html'
	
	form_excluded_columns = (
		'date_created', 'visible'
	)
	
	column_exclude_list = ('visible')
	
	def __init__(self, session, **kwargs):
		super(NewsView, self).__init__(News, session, **kwargs)
		
		
		
		
		