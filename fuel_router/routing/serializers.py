from rest_framework import serializers

class RouteRequestSerializer(serializers.Serializer):
    start_latitude = serializers.FloatField()
    start_longitude = serializers.FloatField()
    finish_latitude = serializers.FloatField()
    finish_longitude = serializers.FloatField()

class FuelStopSerializer(serializers.Serializer):
    station_name = serializers.CharField()
    address = serializers.CharField()
    mile_marker = serializers.FloatField()
    gallons_purchased = serializers.FloatField()
    price_per_gallon = serializers.FloatField()
    leg_cost = serializers.FloatField()

class RouteResponseSerializer(serializers.Serializer):
    total_distance_miles = serializers.FloatField()
    total_fuel_cost = serializers.FloatField()
    route_geometry = serializers.CharField()
    fuel_stops = FuelStopSerializer(many=True)