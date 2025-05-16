from datetime import date
from typing import Tuple
import random
import math
import uuid  # Added for generating unique IDs
from models import KMA, KMA_DEFAULT_COORDINATES, Location, Load


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance in miles between two points
    on the Earth's surface specified by latitude and longitude.

    Args:
        lat1: Latitude of first point in decimal degrees
        lon1: Longitude of first point in decimal degrees
        lat2: Latitude of second point in decimal degrees
        lon2: Longitude of second point in decimal degrees

    Returns:
        Distance between points in miles
    """
    # Earth radius in miles
    R = 3958.8

    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance


def adjust_coordinates_randomly(
    lat: float, lon: float, miles: float = 50
) -> Tuple[float, float]:
    """
    Adjust coordinates randomly within approximately the specified miles.

    Args:
        lat: Base latitude
        lon: Base longitude
        miles: Approximate maximum distance to adjust in miles

    Returns:
        Tuple of adjusted (latitude, longitude)
    """
    # Earth's radius in miles
    R = 3958.8

    # Convert miles to radians (approximate)
    radius = miles / R

    # Random distance within the radius
    distance = random.uniform(0, radius)

    # Random bearing/direction
    bearing = random.uniform(0, 2 * math.pi)

    # Convert to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    # Calculate new position
    lat_new_rad = math.asin(
        math.sin(lat_rad) * math.cos(distance)
        + math.cos(lat_rad) * math.sin(distance) * math.cos(bearing)
    )

    lon_new_rad = lon_rad + math.atan2(
        math.sin(bearing) * math.sin(distance) * math.cos(lat_rad),
        math.cos(distance) - math.sin(lat_rad) * math.sin(lat_new_rad),
    )

    # Convert back to degrees
    lat_new = math.degrees(lat_new_rad)
    lon_new = math.degrees(lon_new_rad)

    return lat_new, lon_new


def generate_random_load(pickup_date: date) -> Load:
    """
    Generate a random Load with the following properties:
    - Random origin KMA with coordinates adjusted randomly
    - Random destination KMA (different from origin) with coordinates adjusted randomly
    - Miles calculated as 1.17 * haversine distance
    - Cost calculated using a random rate between $0.50 and $3.00 per mile
    - Weight randomly chosen between 25000 and 45000 pounds

    Returns:
        A randomly generated Load object
    """
    # Get all available KMAs
    kma_list = list(KMA)

    # Choose different KMAs for origin and destination
    origin_kma = random.choice(kma_list)
    remaining_kmas = [kma for kma in kma_list if kma != origin_kma]
    destination_kma = random.choice(remaining_kmas)

    # Get base coordinates
    origin_base_lat, origin_base_lon = KMA_DEFAULT_COORDINATES[origin_kma]
    destination_base_lat, destination_base_lon = KMA_DEFAULT_COORDINATES[
        destination_kma
    ]

    # Adjust coordinates randomly
    origin_lat, origin_lon = adjust_coordinates_randomly(
        origin_base_lat, origin_base_lon, miles=30
    )
    destination_lat, destination_lon = adjust_coordinates_randomly(
        destination_base_lat, destination_base_lon, miles=30
    )

    # Create locations
    origin_location = Location(
        kma=origin_kma, latitude=origin_lat, longitude=origin_lon
    )
    destination_location = Location(
        kma=destination_kma, latitude=destination_lat, longitude=destination_lon
    )

    # Calculate haversine distance and apply the 1.17 multiplier
    distance = haversine_distance(
        origin_lat, origin_lon, destination_lat, destination_lon
    )
    miles = int(distance * 1.17)

    # Random cost per mile between $0.50 and $3.00
    cost_per_mile = random.uniform(0.50, 3.00)
    total_cost = miles * cost_per_mile

    # Random weight between 25000 and 45000 pounds
    weight = random.randint(25000, 45000)

    # Create and return the Load
    return Load(
        id=str(uuid.uuid4()),
        origin=origin_location,
        destination=destination_location,
        miles=miles,
        pickup_date=pickup_date,
        cost=round(total_cost, 2),
        weight=weight,
    )
