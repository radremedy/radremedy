"""
groupedselectmultiplefield.py

Extends the default SelectMultipleField with widgets
and options that support multi-selection of items in optgroups.

Based on the Gist at:
https://gist.github.com/playpauseandstop/1590178
"""

from wtforms.fields import SelectMultipleField as BaseSelectMultipleField
from wtforms.validators import ValidationError
from wtforms.widgets import HTMLString, html_params, escape
from wtforms.widgets import Select as BaseSelectWidget


__all__ = ('GroupedSelectMultipleField', 'GroupedSelectWidget')


class GroupedSelectWidget(BaseSelectWidget):
    """
    Add support for choices within ``optgroup``s to the ``Select`` widget.
    """
    @classmethod
    def render_option(cls, value, label, mixed):
        """
        Render option as HTML tag, but not forget to wrap options into
        ``optgroup`` tag if ``label`` var is ``list`` or ``tuple``.
        """
        if isinstance(label, (list, tuple)):
            children = []

            for item_value, item_label in label:
                item_html = cls.render_option(item_value, item_label, mixed)
                children.append(item_html)

            html = u'<optgroup label="%s">%s</optgroup>'
            data = (escape(unicode(value)), u'\n'.join(children))
        else:
            coerce_func, data = mixed
            selected = coerce_func(value) == data

            options = {'value': value}

            if selected:
                options['selected'] = u'selected'

            html = u'<option %s>%s</option>'
            data = (html_params(**options), escape(unicode(label)))

        return HTMLString(html % data)


class GroupedSelectMultipleField(BaseSelectMultipleField):
    """
    Add support for ``optgroup``'s' to default WTForms' ``SelectMultipleField`` class.

    So, next choices would be supported as well::

        (
            ('Fruits', (
                ('apple', 'Apple'),
                ('peach', 'Peach'),
                ('pear', 'Pear')
            )),
            ('Vegetables', (
                ('cucumber', 'Cucumber'),
                ('potato', 'Potato'),
                ('tomato', 'Tomato'),
            ))
        )

    """
    # Set up the widget - explicitly pass down multiple=True
    widget = GroupedSelectWidget(multiple=True)

    def iter_choices(self):
        """
        Overrides choice iteration to ensure that optgroups
        are included.
        """
        for value, label in self.choices:
            yield (value, label, (self.coerce, self.data))

    def pre_validate(self, form, choices=None):
        """
        Recurses on validation of choices that are
        contained within embedded iterables.
        """
        default_choices = choices is None
        choices = choices or self.choices

        for value, label in choices:
            found = False

            # If the label in question is itself an iterable
            # (indicating the presence of an optgroup),
            # recurse on the choices in that optgroup.
            if isinstance(label, (list, tuple)):
                found = self.pre_validate(form, label)

            if found or value == self.data:
                return True

        if not default_choices:
            return False

        raise ValidationError(self.gettext(u'Not a valid choice'))
