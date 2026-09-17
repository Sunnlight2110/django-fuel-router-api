from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RouteRequestSerializer, RouteResponseSerializer
from .models import FuelStation
from .pipeline import compute_route_and_fuel_stops

class RouteFuelStopView(APIView):
    def post(self, request):
        req = RouteRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        start_coords = (req.validated_data['start_longitude'], req.validated_data['start_latitude'])
        finish_coords = (req.validated_data['finish_longitude'], req.validated_data['finish_latitude'])

        stations = FuelStation.objects.exclude(latitude__isnull=True)

        try:
            result = compute_route_and_fuel_stops(start_coords, finish_coords, stations)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(RouteResponseSerializer(result).data)