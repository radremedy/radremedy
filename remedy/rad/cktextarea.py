"""
cktextarea.py

A custom field to allow CKEditor-based rich text editing.
"""
from wtforms import fields, widgets

__all__ = ('CKTextAreaField', 'CKTextAreaWidget')


class CKTextAreaWidget(widgets.TextArea):
    """
    A widget for rendering out a multi-line text area as a CKEditor-based
    rich text field.
    """
    def __call__(self, field, **kwargs):
        kwargs['class'] = 'form-control ckeditor'
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(fields.TextAreaField):
    """
    A field for editing multi-line rich text using CKEditor.
    """
    widget = CKTextAreaWidget()
