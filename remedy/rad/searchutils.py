"""

searchutils.py

Contains utility functions for adding normalized searching values
to dictionaries of search parameters.

"""

def add_string(search_params, key, value):
    """
    Adds a string value to the provided search parameters
    dictionary if it is non-empty.

    Args:
        search_params: The parameter dictionary to update.
        key: The key to use.
        value: The value to normalize and use in the dictionary as appropriate.
    """
    if value is None or len(value) == 0 or value.isspace():
        return

    # Stick the trimmed version in the search params
    search_params[key] = value.strip()


def add_bool(search_params, key, value):
    """
    Adds a Boolean value to the provided search parameters
    dictionary if it is non-empty.

    Args:
        search_params: The parameter dictionary to update.
        key: The key to use.
        value: The value to normalize and use in the dictionary as appropriate.
    """
    if value is None or len(value) == 0 or value.isspace():
        return

    # Do a comparison against some basic truth values and
    # treat everything else as false at this point
    search_params[key] = value.strip().lower() in ['true', '1', 'selected', 'on']


def add_int(search_params, key, value, min_value=None, max_value=None):
    """
    Adds an integer value to the provided search parameters
    dictionary if it can be converted.

    Args:
        search_params: The parameter dictionary to update.
        key: The key to use.
        value: The value to normalize and use in the dictionary as appropriate.
        min_value: The minimum value to validate against, if any.
        max_value: The maximum value to validate against, if any.
    """
    if value is None:
        return

    try:
        value_int = int(value)

        # Validation against ranges, if specified
        if min_value is not None and value_int < min_value:
            return

        if max_value is not None and value_int > max_value:
            return

        search_params[key] = value_int
    except ValueError:
        return


def add_int_set(search_params, key, value_list, min_value=None, max_value=None):
    """
    Adds a set of integer values to the provided search parameters
    dictionary if any can be converted.

    Args:
        search_params: The parameter dictionary to update.
        key: The key to use.
        value_list: The list of values to normalize and use in the dictionary as appropriate.
        min_value: The minimum value to validate against, if any.
        max_value: The maximum value to validate against, if any.
    """
    if value_list is None:
        return

    # Initialize an empty set
    int_set = set()

    # Now iterate over the list of values and validate each in turn
    for int_str in value_list:
        try:
            value_int = int(int_str)

            # Validation against ranges, if specified
            if min_value is not None and value_int < min_value:
                continue

            if max_value is not None and value_int > max_value:
                continue

            int_set.add(value_int)
        except ValueError:
            pass

    # If we had any valid values, set the search params key
    if len(int_set) > 0:
        search_params[key] = int_set


def add_float(search_params, key, value, min_value=None, max_value=None):
    """
    Adds a floating-point value to the provided search parameters
    dictionary if it can be converted.

    Args:
        search_params: The parameter dictionary to update.
        key: The key to use.
        value: The value to normalize and use in the dictionary as appropriate.
        min_value: The minimum value to validate against, if any.
        max_value: The maximum value to validate against, if any.
    """
    if value is None:
        return

    try:
        value_float = float(value)

        # Validation against ranges, if specified
        if min_value is not None and value_float < min_value:
            return

        if max_value is not None and value_float > max_value:
            return

        search_params[key] = value_float
    except ValueError:
        return
