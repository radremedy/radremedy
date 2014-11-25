"""
resourceimportview.py

Contains administrative views for importing resources from CSV files.
"""
from admin_helpers import *

import werkzeug.security
from werkzeug.datastructures import MultiDict

from flask import redirect, flash, request, url_for
from flask.ext.login import current_user
from flask.ext.admin import Admin, AdminIndexView, BaseView, expose
from flask.ext.admin.actions import action
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.contrib.fileadmin import FileAdmin
from sqlalchemy import or_, not_, func

from flask_wtf import Form
from wtforms import TextField, StringField, IntegerField, DecimalField, PasswordField, validators, ValidationError

import remedy.data_importer.data_importer
from remedy.rad.db_fun import get_or_create_resource
from remedy.rad.models import Resource, User, Category, Review, db


class ResourceImportFilesView(AdminAuthMixin, FileAdmin):
    """
    A view for .CSV-formatted resource files that can be imported
    into the database.
    """
    # Disable directory manipulation
    can_mkdir = False
    can_delete_dirs = False

    # Use a custom template
    list_template = 'admin/resource_import_list.html'

    def get_actions_list(self):
        """
        Overrides the retrieval of actions to prevent them.
        """
        # Don't allow actions
        return [], {}


class ResourceImportView(AdminAuthMixin, BaseView):
    """
    A view for importing a single .csv resource.
    """
    # Not visible in the menu.
    def is_visible(self):
        return False

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """
        A view for importing resources from a CSV file.
        
        This relies on a filename being provided via a "file"
        query string parameter.

        When actually importing resources via POST, the
        following items are used from the submitted form:
            rowid: A list of the row IDs to import, which
                are indicated on the page via checkboxes.
            create_categories: If true, indicates that new
                categories should be created for each
                resource if it lists any that do not
                already exist. Defaults to false.
            delete_after: If true, indicates that the
                spreadsheet should be deleted after
                a successful import. Defaults to false.

        Returns:
            A view for importing resources from a CSV file.
            This view is provided with the following variables:
                path: The name of the file being imported.
                resource_fields: The names of the fields that
                    will be displayed in the importer.
                resources: A list of the resources that
                    were found in the CSV file. Each resource
                    will have the following fields:
                        row_index: The index of the row, starting with 1.
                        resource: The RadRecord read from the row.
                        valid: A boolean indicating if the record is valid.
                        has_dup_name: A boolean indicating if there were
                            pre-existing resources with the same name.
                        dupes: The existing resources detected as duplicates.
                        
            Upon a valid submission, the user will be
            redirected to the list of CSV files.
        """
        # Get the filename
        filename = request.args.get('file')
        if filename is None or filename == '':
            return resourceimport_redirect()

        # Now normalize it to get the full path
        filepath = werkzeug.security.safe_join(self.basedir, filename)

        # Make sure it exists
        if not op.exists(filepath):
            flash('The file "' + filename + '" does not exist.')
            return resourceimport_redirect()           

        # Let's get down to business. Load up the records.
        radrecords = remedy.data_importer.data_importer.get_radrecords(filepath)

        if len(radrecords) == 0:
            flash('There are no rows in the provided file.')
            return resourceimport_redirect()

        # Figure out which field names to show -
        # filter out category_name because we're using category_names,
        # filter out procedure_type because we're not using it.
        resource_fields = [field for field in radrecords[0]._fields if field not in ('category_name', 'procedure_type')]

        # Get all existing resource names in lowercase
        # and add them to the MultiDict
        existing_resources = self.session.query(Resource).all()
        existing_res_dict = MultiDict()
        for res in existing_resources:
            existing_res_dict.add(res.name.strip().lower(), res)

        # Now wrap each resource in a dict, with additional metadata
        # such as the index of the resource in the list, whether it's
        # valid, and if it has a duplicate name
        row_index = 0
        wrapped_resources = []

        for record in radrecords:
            row_index += 1
            dupe_key = record.name.strip().lower()
            wrapped_resources.append(dict(resource = record, 
                row_index = row_index,
                valid = record.is_valid(), 
                has_dup_name = existing_res_dict.has_key(dupe_key),
                dupes = existing_res_dict.getlist(dupe_key)))

        if request.method == 'GET':
            return self.render('admin/resource_import.html',
                path=filename,
                resources = wrapped_resources,
                resource_fields = resource_fields)
        else:
            row_ids = set([int(id) for id in request.form.getlist('rowid')])

            if len(row_ids) == 0:
                flash('No rows were selected.')
                return self.render('admin/resource_import.html',
                    path=filename,
                    resources = wrapped_resources,
                    resource_fields = resource_fields)

            # Get our other config options.
            create_categories = bool(request.form.get('create_categories', False))
            delete_after = bool(request.form.get('delete_after', False))

            results = []
            had_row_error = False

            # Buckle up. It's time.
            for wrapped_res in wrapped_resources:
                # Build a helpful string to use for messages.
                row_str =  'row #' + str(wrapped_res['row_index']) + ' (' + wrapped_res['resource'].name + ')'

                try:
                    # See if this row is selected and is valid.
                    if wrapped_res['row_index'] in row_ids and wrapped_res['valid']:

                        # Create it and flash a message.
                        get_or_create_resource(self.session,
                            wrapped_res['resource'],
                            create_categories = create_categories)
                        results.append('Imported ' + row_str + '.')

                except Exception as ex:
                    results.append('Error importing ' + row_str + ': ' + str(ex))
                    had_row_error = True

            # Now try to commit everything
            try:
                self.session.commit()
            except Exception as ex:
                results.append('Error committing changes: ' + str(ex))
            else:
                # If specified, clean up afterwards, since we didn't get a fatal error
                if delete_after and not had_row_error:
                    try:
                        os.remove(filepath)
                    except Exception as ex:
                        results.append('The import was successful, but there was an error deleting the file afterwards: ' + str(ex))

            # Flash the results of everything
            flash("\n".join(msg for msg in results))

            return resourceimport_redirect()

    def __init__(self, session, basedir, **kwargs):
        self.session = session
        self.basedir = basedir
        super(ResourceImportView, self).__init__(**kwargs) 
