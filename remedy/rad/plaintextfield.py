"""
plaintextfield.py

A custom field to render out plain text.
"""
# Import either HTML or the CGI escaping function
try:
    from html import escape
except ImportError:
    from cgi import escape

from wtforms.fields import Field

__all__ = ('PlainTextField', 'PlainTextWidget')

class PlainTextWidget():
    def __call__(self, field, **kwargs):
        return '<p class="form-control-static">' + \
            escape(unicode(field.default)) + '</p>'

class PlainTextField(Field):
    # Set up the widget
    widget = PlainTextWidget()

    # Always validate as successful
    def validate(self, form, extra_validators=()):
        return True

    # Always return the default
    def process(self, formdata, data=None):
        self.data = self.default
        return self.default
