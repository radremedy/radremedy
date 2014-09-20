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

        # Make sure we generated something meaningful
        if resource.address is not None and not resource.address.isspace():
            # Now query the geocoder with this formatted string
            geolocator = GoogleV3(api_key=self.api_key)
            new_address, (latitude, longitude) = geolocator.geocode(resource.address)

            # Update the resource based on the returned geopy.location.Location
            if new_address and not new_address.isspace():
                resource.address = new_address

            if latitude and longitude:
                resource.latitude = latitude
                resource.longitude = longitude

        pass
