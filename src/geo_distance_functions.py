from src.load_packages import *

def calculate_distance_in_km(coord1, coord2):
    
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(coord1[0])
    lon1 = radians(coord1[1])
    lat2 = radians(coord2[0])
    lon2 = radians(coord2[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

def vector_calc(lat, long, ht):
    '''
    Calculates the vector from a specified point on the Earth's surface to the North Pole.
    '''
    a = 6378137.0  # Equatorial radius of the Earth
    b = 6356752.314245  # Polar radius of the Earth

    e_squared = 1 - ((b ** 2) / (a ** 2))  # e is the eccentricity of the Earth
    n_phi = a / (np.sqrt(1 - (e_squared * (np.sin(lat) ** 2))))

    x = (n_phi + ht) * np.cos(lat) * np.cos(long)
    y = (n_phi + ht) * np.cos(lat) * np.sin(long)
    z = ((((b ** 2) / (a ** 2)) * n_phi) + ht) * np.sin(lat)

    x_npole = 0.0
    y_npole = 6378137.0
    z_npole = 0.0

    v = ((x_npole - x), (y_npole - y), (z_npole - z))

    return v

def angle_calc(coord1, coord2, ht1=0, ht2=0):
    '''
    Calculates the angle between the vectors from 2 points to the North Pole.
    '''
    # Convert from degrees to radians
    lat1_rad = coord1[0]
    long1_rad = coord1[1]
    lat2_rad = coord2[0]
    long2_rad = coord2[1]

    v1 = vector_calc(lat1_rad, long1_rad, ht1)
    v2 = vector_calc(lat2_rad, long2_rad, ht2)

    # The angle between two vectors, vect1 and vect2 is given by:
    # arccos[vect1.vect2 / |vect1||vect2|]
    dot = np.dot(v1, v2)  # The dot product of the two vectors
    v1_mag = np.linalg.norm(v1)  # The magnitude of the vector v1
    v2_mag = np.linalg.norm(v2)  # The magnitude of the vector v2

    theta_rad = np.arccos(dot / (v1_mag * v2_mag))
    # Convert radians back to degrees
    #theta = (theta_rad / np.pi) * 180
    theta = (theta_rad / np.pi) * 360

    return theta