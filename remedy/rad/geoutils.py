"""

geoutils.py

Contains utility methods for performing geography-related calculations.

Based from the code at http://stackoverflow.com/a/238558

"""

def deg2rad(degrees):
    """
    Converts degrees to radians.

    Args:
        degrees: A degree value.

    Returns:
        The equivalent value in radians.
    """
    return math.pi*degrees/180.0

def rad2deg(radians):
    """
    Converts radians to degrees.

    Args:
        radians: A radians value.

    Returns:
        The equivalent value in degrees.
    """
    return 180.0*radians/math.pi

# Semi-axes of WGS-84 geoidal reference
WGS84_a = 6378137.0  # Major semiaxis [m]
WGS84_b = 6356752.3  # Minor semiaxis [m]

def WGS84EarthRadius(lat):
    """
    Returns the earth radius at a given latitude, according to the
    WGS-84 ellipsoid model (http://en.wikipedia.org/wiki/Earth_radius).

    Args:
        lat: The latitude, in radians.
    
    Returns:
        The Earth radius at the given latitude.
    """
    An = WGS84_a*WGS84_a * math.cos(lat)
    Bn = WGS84_b*WGS84_b * math.sin(lat)
    Ad = WGS84_a * math.cos(lat)
    Bd = WGS84_b * math.sin(lat)
    return math.sqrt( (An*An + Bn*Bn)/(Ad*Ad + Bd*Bd) )

def miles2km(miles):
    """
    Converts miles to kilometers.

    Args:
        miles: A distance in miles.

    Returns:
        The equivalent distance in kilometers.
    """    
    return miles*1.60934

def boundingBox(latitudeInDegrees, longitudeInDegrees, halfSideInKm):
    """
    Calculates the bounding box surrounding the given coordinate point,
    assuming the local approximation of the Earth's surface as a sphere
    of radius determined by WGS84.

    Args:
        latitudeInDegrees: The latitude of the point, in degrees.
        longitudeInDegrees: The longitude of the point, in degrees.
        halfSideInKm: Half the length/width of the desired bounding box, in kilometers.

    Returns:
        A bounding box of coordinates, provided in the order of
        minimum latitude, minimum longitude, maximum latitude, and maximum longitude.
    """
    lat = deg2rad(latitudeInDegrees)
    lon = deg2rad(longitudeInDegrees)
    halfSide = 1000*halfSideInKm # Convert to meters

    # Radius of Earth at given latitude
    radius = WGS84EarthRadius(lat)
    # Radius of the parallel at given latitude
    pradius = radius*math.cos(lat)

    latMin = lat - halfSide/radius
    latMax = lat + halfSide/radius
    lonMin = lon - halfSide/pradius
    lonMax = lon + halfSide/pradius

    return (rad2deg(latMin), rad2deg(lonMin), rad2deg(latMax), rad2deg(lonMax))
