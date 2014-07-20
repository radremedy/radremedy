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
        # Turn the different address components into a formatted string
        search_address = ", ".join(a for a in [resource.street,
                                    resource.city, resource.state,
                                    resource.zipcode, resource.country]
                                    if a is not None and not
                                    a.isspace())

        # Make sure we generated something meaningful
        if search_address and search_address is not None:
            # Now query the geocoder with this formatted string
            geolocator = GoogleV3(api_key=self.api_key)
            address, (latitude, longitude) = geolocator.geocode(search_address)

            # Update the resource based on the returned geopy.location.Location
            if address and not address.isspace():
                resource.fulladdress = address

            if latitude and longitude:
                resource.latitude = latitude
                resource.longitude = longitude

            # FUTURE: Perform additional normalization operations based
            # on the information in Location.raw
        pass
