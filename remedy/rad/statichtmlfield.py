"""
statichtmlfield.py

A custom field to render out static HTML.
"""
from wtforms.fields import Field

__all__ = ('StaticHtmlField', 'StaticHtmlWidget')

class StaticHtmlWidget():
    def __call__(self, field, **kwargs):
        return '<p class="form-control-static">' + \
            unicode(field.default) + '</p>'

class StaticHtmlField(Field):
    # Set up the widget
    widget = StaticHtmlWidget()

    # Always validate as successful
    def validate(self, form, extra_validators=()):
        return True

    # Always return the default
    def process(self, formdata, data=None):
        self.data = self.default
        return self.default
