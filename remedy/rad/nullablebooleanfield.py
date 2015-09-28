"""
nullablebooleanfield.py

A custom field, rendered as a dropdown, to represent a nullable
Boolean with true, false, and N/A or Unknown options.
"""
from wtforms.fields import Field
from wtforms.widgets import Select as BaseSelectWidget


__all__ = ('NullableBooleanField')


class NullableBooleanField(Field):
    # Set up the widget
    widget = BaseSelectWidget()

    # Store our Boolean choices - this is a list of
    # (HTML value, HTML label, Python value) tuples
    tri_boolean_choices = [
        ('', 'N/A or Unknown', None),
        ('True', 'True', True),
        ('False', 'False', False)
    ]

    def iter_choices(self):
        """
        Iterates over tri-state tuples for the provided value.
        """
        for value, label, pyvalue in self.tri_boolean_choices:
            # This is intentionally a reference comparison,
            # instead of a value comparison - we don't want
            # "None" and "False" equivalence.
            yield (value, label, self.data is pyvalue)

    def process_formdata(self, valuelist):
        """
        Converts incoming form data to a nullable boolean value.
        """
        # See if we actually have a string.
        if valuelist and len(valuelist) > 0 and valuelist[0]:
            # We have a string so we know it's either true or false.
            # Check for "true" equality.
            self.data = valuelist[0].strip().lower() == "true"
        else:
            self.data = None
