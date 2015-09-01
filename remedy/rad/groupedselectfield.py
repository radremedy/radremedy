"""
groupedselectfield.py

Extends the default SelectMultipleField with widgets
and options that support multi-selection of items in optgroups.

Based on the Gist at:
https://gist.github.com/playpauseandstop/1590178
"""
# Import either HTML or the CGI escaping function
try:
    from html import escape
except ImportError:
    from cgi import escape

from wtforms.fields import SelectMultipleField as BaseSelectMultipleField
from wtforms.validators import ValidationError
from wtforms.widgets import HTMLString, html_params
from wtforms.widgets import Select as BaseSelectWidget


__all__ = ('GroupedSelectMultipleField', 'GroupedSelectWidget')


class GroupedSelectWidget(BaseSelectWidget):
    """
    Add support for choices within ``optgroup``s to the ``Select`` widget.
    """
    @classmethod
    def render_option(cls, value, label, mixed):
        """
        Renders an option as the appropriate element,
        but wraps options into an ``optgroup`` tag
        if the ``label`` parameter is ``list`` or ``tuple``.

        The last option, mixed, differs from "selected" in that
        it is a tuple containing the coercion function, the
        current field data, and a flag indicating if the
        associated field supports multiple selections.
        """
        # See if this label is actually a group of items
        if isinstance(label, (list, tuple)):
            children = []

            # Iterate on options for the children.
            for item_value, item_label in label:
                item_html = cls.render_option(item_value, item_label, mixed)
                children.append(item_html)

            html = u'<optgroup %s>%s</optgroup>\n'
            data = (html_params(label=unicode(value)), u''.join(children))
        else:
            # Get our coercion function, the field data, and
            # a flag indicating if this is a multi-select from the tuple
            coerce_func, fielddata, multiple = mixed

            # See if we have field data - if not, don't bother
            # to see if something's selected.
            if fielddata is not None:
                # If this is a multi-select, look for the value
                # in the data array. Otherwise, look for an exact
                # value match.
                if multiple:
                    selected = coerce_func(value) in fielddata
                else:
                    selected = coerce_func(value) == fielddata
            else:
                selected = False

            options = {'value': value}

            if selected:
                options['selected'] = True

            html = u'<option %s>%s</option>\n'
            data = (html_params(**options), escape(unicode(label)))

        return HTMLString(html % data)


class GroupedSelectMultipleField(BaseSelectMultipleField):
    """
    Add support for ``optgroup``'s' to WTForms' ``SelectMultipleField`` class.

    This supports choices in the following format:

    [
        ('ID1', 'Ungrouped Item 1'),
        ('ID2', 'Ungrouped Item 2'),
        (
            'Group 1',
            [
                ('ID3', 'Item A in Group 1'),
                ('ID4', 'Item B in Group 1')
            ]
        ),
        (
            'Group 2',
            [
                ('ID4', 'Item C in Group 2'),
                ('ID5', 'Item D in Group 2')
            ]
        )
    ]
    """
    # Set up the widget - explicitly pass down multiple=True
    widget = GroupedSelectWidget(multiple=True)

    def iter_choices(self):
        """
        Overrides choice iteration to ensure that optgroups
        are included.
        """
        for value, label in self.choices:
            # Instead of passing in a selected boolean,
            # pass in a mixed tuple for value coercion in addition
            # to the field data and a value indicating if we support
            # multiple selections (which is always true for this field)
            yield (value, label, (self.coerce, self.data, True))

    def pre_validate(self, form, choices=None):
        """
        Recurses on validation of choices that are
        contained within embedded iterables.
        """
        # See if we have default choices
        default_choices = choices is None

        # If we have choices provided (true for recursion on groups),
        # use those - otherwise, default to the top-level field choices.
        choices = choices or self.choices

        for value, label in choices:
            found = False

            # If the label in question is itself an iterable
            # (indicating the presence of an optgroup),
            # recurse on the choices in that optgroup.
            if isinstance(label, (list, tuple)):
                found = self.pre_validate(form, choices=label)

            # The second part of this also differs from the Gist -
            # we want to check value in self.data instead of value == self.data
            if found or value in self.data:
                return True

        # If we don't have any default choices at this point,
        # there's not really anything we can do.
        if not default_choices:
            return False

        raise ValidationError(self.gettext(u'Not a valid choice'))
