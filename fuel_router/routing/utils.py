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

ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"

def geocode_location(location_str):
    """
    location_str: free-text address/city, e.g. "Chicago, IL"
    Returns: (lng, lat) tuple — ORS coordinate order
    """
    params = {
        'api_key': ORS_API_KEY,
        'text': location_str,
        'boundary.country': 'US',
        'size': 1,
    }
    response = requests.get(ORS_GEOCODE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    features = data.get('features', [])
    if not features:
        raise ValueError(f"Could not geocode location: {location_str}")

    lng, lat = features[0]['geometry']['coordinates']
    return (lng, lat)