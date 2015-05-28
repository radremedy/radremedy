"""
data_importer.py

Manages the location of the saved .csv files. 
"""

from toolz import partial
from radrecord import rad_record
import unicodecsv
import os

# force python lazy functions to act
force = list


def open_dict_csv(file_path):
    """
    Opens a CSV file and returns a dictionary reader.

    Args:
        file_path: The path to the CSV file.

    Returns:
        A dictionary reader for the CSV file.
    """
    csvfile = None
    try:
        # Read the CSV
        csvfile = open(file_path, 'r')

        # Get the equivalent reader
        return unicodecsv.DictReader(csvfile)
    except unicodecsv.csv.Error:
        # In the event of a CSV error, close the file handle
        if csvfile is not None:
            csvfile.close()

def filter_keys(d, key_whitelist):
    """
    Removes keys from a dictionary that are not
    in the provided whitelist.

    Args:
        d: The dictionary to update.
        key_whitelist: The list of allowed keys.
    
    Returns:
        The updated dictionary.
    """
    for key in d.keys():
        if key not in key_whitelist:
            d.pop(key)

    return d


def rename_key(d, oldkey, newkey):
    """
    Renames a key/value pair in a dictionary.

    Args:
        d: The dictionary to update.
        oldkey: The old key to rename.
        newkey: The new name of the key.

    Returns:
        The updated dictionary.
    """
    if oldkey in d:
        value = d.pop(oldkey)
        d[newkey] = value

    return d


def get_radrecord(d, resource_fields):
    """
    Gets the equivalent RadRecord from the
    provided dictionary. Will perform category normalization.

    Args:
        d: The source dictionary.
        resource_fields: The list of fields that are recognized
            by the RadRecord.

    Returns:
        The equivalent RadRecord.
    """
    # Perform normalization - map "category" to
    # "category_name" and filter out unrecognized fields
    # afterwards
    filtered_dict = rename_key(d, 'category', 'category_name') 
    filtered_dict = filter_keys(filtered_dict, resource_fields)

    # Now create a RadRecord from the dict and normalize
    # the categories.
    return rad_record(**filtered_dict).convert_category_name()


def get_radrecords(file_path):
    """
    Opens a CSV file and returns the equivalent
    RadRecords.

    Args:
        file_path: The path to the CSV file.

    Returns:
        The RadRecords in the file.
    """
    # Create a new RadRecord so we can get the field names
    dummy_record = rad_record(name='Ministry of Silly Walks')
    resource_fields = dummy_record._fields

    # Now get resources from each row
    return map(lambda row: get_radrecord(row, resource_fields),
        open_dict_csv(file_path))


# This is the location of your local copy
# of our Drop box folder with the data on it
# for example on my computer it is: /home/wil/Data/Trans
# export RAD_DATA_BASE="/home/wil/Data/Trans"
BASE_DATA_DIR = os.environ.get('RAD_DATA_BASE')
data_dir = partial(os.path.join, BASE_DATA_DIR)

