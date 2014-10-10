"""
data_importer.py

Manages the location of the saved .csv files. 
"""

from toolz import unique, partial
import csv
import os

# force python lazy functions to act
force = list


def open_csv(file_path, skip_head=True):
    """
    TODO: write this docstring 
    """
    f = csv.reader(open(file_path, 'r'))

    if skip_head:
        next(f)

    return f


def open_dict_csv(file_path):
    """
    TODO: write this docstring 
    """
    return csv.DictReader(open(file_path, 'r'))


def minus_key(d, k):
    """
    Removes a key/value pair from a dictionary.

    Args:
        d: The dictionary to update.
        k: The key of the value to remove.

    Returns:
        The updated dictionary.
    """
    d.pop(k)
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

def unique_from_column(n, columns):
    """
    TODO: write this docstring 
    """
    return unique([row[n] for row in columns])

zeroth = partial(unique_from_column, 0)
firsts = partial(unique_from_column, 1)
seconds = partial(unique_from_column, 2)
thirds = partial(unique_from_column, 3)
fourths = partial(unique_from_column, 4)
fifths = partial(unique_from_column, 5)
sixths = partial(unique_from_column, 6)
sevenths = partial(unique_from_column, 7)
eighths = partial(unique_from_column, 8)
ninths = partial(unique_from_column, 9)

# This is the location of your local copy
# of our Drop box folder with the data on it
# for example on my computer it is: /home/wil/Data/Trans
# export RAD_DATA_BASE="/home/wil/Data/Trans"
BASE_DATA_DIR = os.environ.get('RAD_DATA_BASE')
data_dir = partial(os.path.join, BASE_DATA_DIR)

