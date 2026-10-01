from math import radians, sin, cos, sqrt, atan2

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Product, FuelStation
from .serializers import ProductSerializer, FuelStationSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class FuelStationViewSet(viewsets.ModelViewSet):
    queryset = FuelStation.objects.all()
    serializer_class = FuelStationSerializer

    def get_queryset(self):
        queryset = FuelStation.objects.all()

        state = self.request.query_params.get("state")
        city = self.request.query_params.get("city")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        ordering = self.request.query_params.get("ordering")

        # Filter by state
        if state:
            queryset = queryset.filter(state__iexact=state)

        # Filter by city
        if city:
            queryset = queryset.filter(city__iexact=city)

        # Filter by minimum price
        if min_price:
            queryset = queryset.filter(retail_price__gte=min_price)

        # Filter by maximum price
        if max_price:
            queryset = queryset.filter(retail_price__lte=max_price)

        # Sort by retail price
        if ordering == "retail_price":
            queryset = queryset.order_by("retail_price")

        elif ordering == "-retail_price":
            queryset = queryset.order_by("-retail_price")

        return queryset

    @action(detail=False, methods=["get"])
    def nearby(self, request):
        latitude = request.query_params.get("latitude")
        longitude = request.query_params.get("longitude")
        radius = request.query_params.get("radius", 10)

        if not latitude or not longitude:
            return Response(
                {
                    "error": "latitude and longitude are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            latitude = float(latitude)
            longitude = float(longitude)
            radius = float(radius)
        except ValueError:
            return Response(
                {
                    "error": "latitude, longitude and radius must be numbers."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if radius <= 0:
            return Response(
                {
                    "error": "radius must be greater than 0."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        stations = FuelStation.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
        )

        nearby_stations = []

        # Haversine distance calculation
        earth_radius_km = 6371.0

        user_lat = radians(latitude)
        user_lon = radians(longitude)

        for station in stations:
            station_lat = radians(station.latitude)
            station_lon = radians(station.longitude)

            delta_lat = station_lat - user_lat
            delta_lon = station_lon - user_lon

            a = (
                sin(delta_lat / 2) ** 2
                + cos(user_lat)
                * cos(station_lat)
                * sin(delta_lon / 2) ** 2
            )

            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            distance = earth_radius_km * c

            if distance <= radius:
                nearby_stations.append(
                    {
                        "id": station.id,
                        "truckstop_name": station.truckstop_name,
                        "city": station.city,
                        "state": station.state,
                        "retail_price": station.retail_price,
                        "latitude": station.latitude,
                        "longitude": station.longitude,
                        "distance_km": round(distance, 2),
                    }
                )

        nearby_stations.sort(
            key=lambda station: station["distance_km"]
        )

        return Response(nearby_stations)


