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
    if value is None or value.isspace():
        return

    # Stick the trimmed version in the search params
    search_params[key] = value.strip()

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
