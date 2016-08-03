from geopy.geocoders import GoogleV3


class Geocoder:
    """
    Contains functionality for performing geocoding operations on locations.

    Attributes:
        api_key: An API key to be used with the external geocoding service.
    """

    def __init__(self, api_key=None):
        """Initializes the geocoder with the provided API key."""
        self.api_key = api_key

    def get_comp(self, addr_comp, key):
        """
        Gets the provided string, indicated by key, in the
        provided dictionary of address components if it exists.

        Args:
            addr_comp: The dictionary of address components.
            key: The key of the component to retrieve.

        Returns:
            The specified address component, or None if it does not exist.
        """
        if key in addr_comp and \
                len(addr_comp[key]) > 0 and \
                not addr_comp[key].isspace():
            return addr_comp[key]

        return None

    def get_locality_strings(self, address_components):
        """
        Gets a tuple of city/county/state strings from the provided
        collection of address components.

        Args:
            The collection of address components to search.

        Returns:
            A tuple in the form of city, county, and state strings,
            in that order.
        """
        city_str = ''
        county_str = ''
        state_str = ''

        for addr_comp in address_components:
            name_str = ''

            # Figure out which name to use (prefer short)
            name_str = \
                self.get_comp(addr_comp, 'short_name') or \
                self.get_comp(addr_comp, 'long_name')

            # Make sure we have something
            if not name_str or name_str.isspace():
                continue

            # Make sure we have types
            if addr_comp.get('types') is None or \
                    len(addr_comp['types']) == 0:
                continue

            # Now look for a match, but only update using
            # name_str if we don't have something already.
            # locality - city
            # administrative_area_level_2 - county
            # administrative_area_level_1 - state/province
            for comp_type in addr_comp['types']:
                if comp_type == 'locality':

                    # Issue 227 - prefer long_name if we have
                    # it for cities ("Chicago"/"Los Angeles"
                    # is better than "Chgo"/"LA")
                    if self.get_comp(addr_comp, 'long_name'):
                        name_str = addr_comp['long_name']

                    city_str = city_str or name_str
                elif comp_type == 'administrative_area_level_2':
                    county_str = county_str or name_str
                elif comp_type == 'administrative_area_level_1':
                    state_str = state_str or name_str

        # Convert city/county/state into a tuple
        return (city_str, county_str, state_str)

    def geocode(self, resource):
        """
        Performs geocoding on the provided resource and updates its formatted
        address, latitude, and longitude.

        Args:
            resource: A resource from which the address components will be
                retrieved and used to update its formatted address,
                latitude, and longitude.

        Raises:
            geopy.exc.GeopyError: An error occurred attempting to access the
                geocoder.
        """

        # Make sure we generated something meaningful
        if resource.address is not None and not resource.address.isspace():
            # Now query the geocoder with this formatted string
            geolocator = GoogleV3(api_key=self.api_key)

            new_location = geolocator.geocode(
                resource.address,
                exactly_one=True)

            if new_location is not None:
                new_res_location = ''

                if new_location.address and \
                        not new_location.address.isspace():
                    resource.address = new_location.address

                if new_location.latitude is not None and \
                        new_location.longitude is not None:
                    resource.latitude = new_location.latitude
                    resource.longitude = new_location.longitude

                # Look at the raw response for address components
                if new_location.raw:
                    address_components = new_location.raw.get(
                        'address_components')

                    if address_components:
                        # Get the city/county/state strings
                        city_str, county_str, state_str = \
                            self.get_locality_strings(address_components)

                        # Now build the location based on those strings,
                        # preferring city to county
                        new_res_location = city_str or county_str or ''

                        if state_str:
                            # Add a comma and space between the city/county
                            # and state
                            if new_res_location:
                                new_res_location = new_res_location + ', '

                            new_res_location = new_res_location + state_str

                # After all of that, update the location
                resource.location = new_res_location
        pass
