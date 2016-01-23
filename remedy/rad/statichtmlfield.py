"""
statichtmlfield.py

A custom field to render out static HTML.
"""
from wtforms.fields import Field

__all__ = ('StaticHtmlField', 'StaticHtmlWidget')


class StaticHtmlWidget():
    """
    A widget for rendering out static HTML wrapped in a
    p.form-control-static element.
    """
    def __call__(self, field, **kwargs):
        return '<p class="form-control-static">' + \
            unicode(field.default) + '</p>'


class StaticHtmlField(Field):
    """
    A field for displaying static HTML. This field's value
    cannot be changed and always uses the default.
    """
    # Set up the widget
    widget = StaticHtmlWidget()

    # Always validate as successful
    def validate(self, form, extra_validators=()):
        return True

    # Always return the default
    def process(self, formdata, data=None):
        self.data = self.default
        return self.default
