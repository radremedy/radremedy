"""
forms.py

Contains general-purpose forms, such as those for contacting
the RAD team about resource corrections, reviewing resources,
and changing user settings.
"""

from flask.ext.login import current_user
from flask_wtf import Form

from wtforms import StringField, TextAreaField, SubmitField, ValidationError, \
    HiddenField, SelectField, SelectMultipleField, RadioField, DecimalField
from wtforms.widgets import HiddenInput
from wtforms.validators import InputRequired, EqualTo, Length, Regexp, \
    Email, URL, Optional

from .groupedselectfield import GroupedSelectMultipleField
from .nullablebooleanfield import NullableBooleanField

from .models import Resource, User, Population

class SubmitProviderBaseForm(object):
    """
    A mixin that contains all form fields needed for provider entry.
    """
    provider_name = StringField('Provider Name', 
        description='Formatting: First Name Last Name, Titles (ex. Jane Smith, LCSW)\n' +
        'If this is an organization, please put its name in this box',
        validators=[
        InputRequired(), 
        Length(5, 250)
    ])

    organization_name = StringField('Organization Name', 
        description='Formatting: Organization Name (ex. Sage Community Health Collective)\n' +
        'If you wish to recommend the whole organization as opposed to a specific person there, please put the organization name in the "Provider Name" box.',
        validators=[
        Optional(), 
        Length(0, 500)
    ])

    description = TextAreaField('Description of Provider/Provider Services',
        description='This is a brief description of an organization, such as a mission statement or similar.\n' + 
        'If this is not obvious when you are trying to fill in the blanks, do not worry about it and leave it blank.',
        validators=[
        Optional()
    ])

    address = StringField('Address', 
        validators=[
        Optional(), 
        Length(0, 500)
    ])

    phone_number = TextAreaField('Phone Number',
        description='Formatting: (555) 555-5555',
        validators=[
        Optional(),
        Length(0, 50)
    ])

    fax_number = TextAreaField('Fax Number',
        description='Formatting: (555) 555-5555',
        validators=[
        Optional(),
        Length(0, 50)
    ]) 

    email = StringField('Email', 
        validators=[
        Optional(), 
        Email(), 
        Length(0, 250)
    ])

    website = StringField('Website', 
        description='If available.',
        validators=[
        Optional(), 
        URL(), 
        Length(0, 500)
    ])

    office_hours = TextAreaField('Office Hours',
        description='If available.\n' + 
        'Specific Formatting: Days: Mon, Tues, Wed, Thurs, Fri, Sat, Sun; Hours: 9 am - 4:30 pm. Extra Specifics: (Walk-ins)\n' +
        'Long Formatting Example: Mon, Tues, Wed - 9 am - 4:30 pm (By Appointment Only); Thurs-Sat - 10:30 am - 7 pm (Appointments and Walk-ins); Sun - Closed',
        validators=[
        Optional()
    ])

    categories = GroupedSelectMultipleField(label='Type(s) of Service(s)', coerce=int, 
        description='Check all that may apply. Please answer to the best of your ability.\n' +
        'If a desired option is not available, please specify in the "Other Notes" section below.',
        validators=[
        Optional()
    ])

    populations = GroupedSelectMultipleField(label='Population(s) Served', coerce=int, 
        description='Some providers/organizations only serve youth or seniors, ' +
        'or sometimes they serve lots of groups. but have a special focus on XYZ, ' + 
        'which can include gender, race, age, religion, etc.\n' +
        'If they specify, list that here.',
        validators=[
        Optional()
    ])

    hospital_affiliation = TextAreaField('Hospital Affiliations',
        description='Is this provider tied to certain hospitals?\n' + 
        'This can include admitting privileges, administrative connections, ' + 
        'where they perform operations, etc.',
        validators=[
        Optional()
    ])

    is_icath = NullableBooleanField('Informed Consent/ICATH?',
        description='Does the provider use the informed consent model?\n' +
        'More information about informed consent is available at http://www.icath.org/',
        validators=[
        Optional()
    ])

    is_wpath = NullableBooleanField('WPATH Provider?',
        description='Is the provider a member of the WPATH organization?\n' +
        'More information about WPATH is available at http://www.wpath.org/',
        validators=[
        Optional()
    ])

    is_accessible = NullableBooleanField('ADA/Handicap Accessible?',
        validators=[
        Optional()
    ])

    has_sliding_scale = NullableBooleanField('Has Sliding Fee Scale?',
        description='Does the provider have a sliding fee scale?',
        validators=[
        Optional()
    ])

    npi = StringField('NPI (National Provider Identifier) Number',
        description='This is something that would need to be looked up.\n' + 
        'You can find the number by doing a search here: http://npidb.org/npi-lookup/\n' +
        'If you can\'t find it or don\'t have the time to look it up, please don\'t worry about it.',
        validators=[
        Optional(),
        Regexp('^\d{10}$', 0, 'The NPI number must be a 10-digit number.')
    ])

    other_notes = TextAreaField('Other Notes',
        description='We will eventually be expanding the database to have more information ' +
        'and it would be helpful to have all known information about this provider available.\n' +
        'Please list anything that is provided that did not fit into the above questions, ' +
        'such as insurance(s) accepted, other languages spoken, etc.',
        validators=[
        Optional()
    ])


class ReviewBaseForm(object):
    """
    A mixin that contains all form fields needed for review entry.
    """
    rating = RadioField('Provider Experience', choices=[
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
    ], validators=[
        InputRequired()
    ])

    intake_rating = RadioField('Intake Experience', default='0', choices=[
        ('0', 'N/A'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
    ], validators=[
        InputRequired()
    ])

    staff_rating = RadioField('Staff Experience', default='0', choices=[
        ('0', 'N/A'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
    ], validators=[
        InputRequired()
    ])

    review_comments = TextAreaField('Comments',
        description='Leave any other comments about the provider here!\nThis is limited to 5,000 characters.', 
        validators=[
        InputRequired(), 
        Length(1, 5000)
    ])

class ContactForm(Form):
    """
    A form for submitting a correction to a resource.

    Fields on the form:
        message
    """
    message = TextAreaField("Message", validators=[
        InputRequired("A message is required.")
    ])

    submit = SubmitField("Send")

class UserSubmitProviderForm(ReviewBaseForm, SubmitProviderBaseForm, Form):
    """
    A form for individuals to submit new resources, coupled with a review.

    Fields on the form:
        provider_name (inherited from provider mixin)
        organization_name (inherited from provider mixin)
        description (inherited from provider mixin)
        address (inherited from provider mixin)
        phone_number (inherited from provider mixin)
        fax_number (inherited from provider mixin)
        email (inherited from provider mixin)
        website (inherited from provider mixin)
        office_hours (inherited from provider mixin)
        categories (inherited from provider mixin)
        populations (inherited from provider mixin)
        hospital_affiliation (inherited from provider mixin)
        is_icath (inherited from provider mixin)
        is_wpath (inherited from provider mixin)
        is_accessible (inherited from provider mixin)
        has_sliding_scale (inherited from provider mixin)
        npi (inherited from provider mixin)
        other_notes (inherited from provider mixin)
        rating (inherited from review mixin)
        intake_rating (inherited from review mixin)
        staff_rating (inherited from review mixin)
        review_comments (inherited from review mixin)
    """
    submit = SubmitField("Submit Provider")

    def __init__(self, formdata, obj, 
        grouped_category_choices, grouped_population_choices):
        super(UserSubmitProviderForm, self).__init__(formdata=formdata, obj=obj)
        
        # Pass in our grouped categories/populations verbatim
        self.categories.choices = grouped_category_choices
        self.populations.choices = grouped_population_choices

        # Set the default and force a re-analysis of categories/populations 
        # *without* the underlying object (i.e. only with form data), 
        # because WTForms doesn't know how to translate the collections into
        # appropriate defaults from the obj instance.
        self.categories.default = [c.id for c in obj.categories]
        self.categories.process(formdata)

        self.populations.default = [p.id for p in obj.populations]
        self.populations.process(formdata)


class ReviewForm(ReviewBaseForm, Form):
    """
    A form for submitting resource reviews.

    Fields on the form:
        rating (inherited from review mixin)
        intake_rating (inherited from review mixin)
        staff_rating (inherited from review mixin)
        review_comments (inherited from review mixin)
        provider (Hidden)
    """
    # the Resource been reviewed, this field is hidden
    # because we set in the templates, the user
    # doesn't actually have to select this
    provider = HiddenField(validators=[
        InputRequired()
    ])

    submit = SubmitField('Submit Review')

    def validate_provider(self, field):
        """
        Validates that the provider exists in the database
        and is visible/approved.
        """
        provider = Resource.query. \
            filter(Resource.id == field.data). \
            filter(Resource.visible == True). \
            filter(Resource.is_approved == True). \
            first()

        if provider is None:
            raise ValidationError('No provider found.')


class UserSettingsForm(Form):
    """
    A form for submitting resource reviews.

    Fields on the form:
        email
        display_name
        default_location
        default_latitude (Hidden)
        default_longitude (Hidden)
        populations
    """
    email = StringField('Email', validators=[
        InputRequired(), 
        Email(), 
        Length(1, 70)
    ])

    display_name = StringField('Displayed Name', 
        description='This is the name that will be displayed with any of your reviews.',
        validators=[
        InputRequired(), 
        Length(2, 100)
    ])

    default_location = StringField('Default Location', 
        description='By default, this location will be used when you search for resources.',
        validators=[
        Optional(), 
        Length(0, 500)
    ])
    
    default_latitude = DecimalField(widget=HiddenInput(), validators=[
        Optional()
    ])
    
    default_longitude = DecimalField(widget=HiddenInput(), validators=[
        Optional()
    ])

    populations = GroupedSelectMultipleField(label='Identities (Optional)', coerce=int, 
        description='Choose any number of identities to which you feel you belong.\n' +
            'This helps tailor any review scores to individuals, including yourself, with similar identities.',
        validators=[
        Optional()
    ])

    submit = SubmitField('Save')

    def __init__(self, formdata, obj, grouped_population_choices):
        super(UserSettingsForm, self).__init__(formdata=formdata, obj=obj)
        
        # Pass in our grouped populations verbatim
        self.populations.choices = grouped_population_choices

        # Set the default and force a re-analysis of populations *without* the
        # underlying object (i.e. only with form data), because WTForms
        # doesn't know how to translate the populations collection into
        # appropriate defaults from the obj instance.
        self.populations.default = [p.id for p in obj.populations]
        self.populations.process(formdata)

    def validate_email(self, field):
        """
        Validates that the provided email is unique.
        """
        existing_user = User.query. \
            filter(User.email == field.data). \
            filter(User.id != current_user.id). \
            first()

        if existing_user:
            raise ValidationError('A user already exists in the database with that email.')
