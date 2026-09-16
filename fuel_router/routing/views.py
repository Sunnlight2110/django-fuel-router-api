from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RouteRequestSerializer, RouteResponseSerializer
import time
from .models import FuelStation
from .pipeline import compute_route_and_fuel_stops
from .utils import geocode_location

class RouteFuelStopView(APIView):
    def post(self, request):
        req = RouteRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        try:
            start_coords = geocode_location(req.validated_data['start_location'])
            finish_coords = geocode_location(req.validated_data['finish_location'])
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        t_request_start = time.perf_counter()

        t_db = time.perf_counter()
        stations = FuelStation.objects.exclude(latitude__isnull=True)
        t_db_after = time.perf_counter()
        print(f"[PERF] Station DB query/filtering: {t_db_after - t_db:.3f}s")

        try:
            result = compute_route_and_fuel_stops(start_coords, finish_coords, stations)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        t_request_end = time.perf_counter()
        print(f"[PERF] TOTAL (request): {t_request_end - t_request_start:.3f}s")

        return Response(RouteResponseSerializer(result).data)