import requests
from fuel_router.settings import ORS_API_KEY

ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"


def get_route(start_coords, end_coords):
    """
    start_coords, end_coords: tuples of (longitude, latitude)
    Note: ORS expects [lng, lat] order, NOT [lat, lng]
    Returns: dict with distance_miles, geometry (route line), raw response
    """
    headers = {
        'Authorization': ORS_API_KEY,
        'Content-Type': 'application/json',
    }
    body = {
        "coordinates": [list(start_coords), list(end_coords)]
    }

    response = requests.post(ORS_BASE_URL, json=body, headers=headers)
    response.raise_for_status()
    data = response.json()

    route = data['routes'][0]
    distance_meters = route['summary']['distance']
    distance_miles = distance_meters / 1609.34

    return {
        'distance_miles': distance_miles,
        'geometry': route['geometry'],  # encoded polyline
        'raw': data,
    }