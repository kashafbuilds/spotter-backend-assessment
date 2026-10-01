import math

import requests
from decouple import config
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import FuelStation, Product
from .serializers import FuelStationSerializer, ProductSerializer


MAX_RANGE_MILES = 500.0
FUEL_ECONOMY_MPG = 10.0
ROUTE_CORRIDOR_MILES = 50.0


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two coordinates in miles.
    """
    earth_radius_miles = 3958.7613

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.asin(math.sqrt(a))

    return earth_radius_miles * c


def distance_to_route(point, route_coordinates):
    """
    Approximate the distance from a station to the route.

    The route is represented by coordinate points. For simplicity,
    the minimum Haversine distance to the route points is used.
    """
    lat, lon = point

    if not route_coordinates:
        return float("inf")

    return min(
        haversine_distance(
            lat,
            lon,
            coordinate[1],
            coordinate[0],
        )
        for coordinate in route_coordinates
    )


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class FuelStationViewSet(viewsets.ModelViewSet):
    queryset = FuelStation.objects.all().order_by("id")
    serializer_class = FuelStationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        state = self.request.query_params.get("state")
        city = self.request.query_params.get("city")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if state:
            queryset = queryset.filter(state__iexact=state)

        if city:
            queryset = queryset.filter(city__iexact=city)

        if min_price:
            try:
                queryset = queryset.filter(
                    retail_price__gte=float(min_price)
                )
            except ValueError:
                pass

        if max_price:
            try:
                queryset = queryset.filter(
                    retail_price__lte=float(max_price)
                )
            except ValueError:
                pass

        ordering = self.request.query_params.get("ordering")

        if ordering in {
            "retail_price",
            "-retail_price",
            "city",
            "-city",
            "state",
            "-state",
        }:
            queryset = queryset.order_by(ordering, "id")

        return queryset

    @action(detail=False, methods=["get"])
    def nearby(self, request):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        radius_km = request.query_params.get("radius_km", "50")

        if lat is None or lon is None:
            return Response(
                {
                    "error": "lat and lon are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lat = float(lat)
            lon = float(lon)
            radius_km = float(radius_km)
        except ValueError:
            return Response(
                {
                    "error": "lat, lon, and radius_km must be valid numbers."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (-90 <= lat <= 90):
            return Response(
                {
                    "error": "lat must be between -90 and 90."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (-180 <= lon <= 180):
            return Response(
                {
                    "error": "lon must be between -180 and 180."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if radius_km <= 0:
            return Response(
                {
                    "error": "radius_km must be greater than 0."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        radius_miles = radius_km * 0.621371

        stations = FuelStation.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
        )

        nearby_stations = []

        for station in stations:
            distance_miles = haversine_distance(
                lat,
                lon,
                station.latitude,
                station.longitude,
            )

            if distance_miles <= radius_miles:
                nearby_stations.append(
                    {
                        "id": station.id,
                        "opis_truckstop_id": station.opis_truckstop_id,
                        "truckstop_name": station.truckstop_name,
                        "address": station.address,
                        "city": station.city,
                        "state": station.state,
                        "retail_price": float(station.retail_price),
                        "latitude": station.latitude,
                        "longitude": station.longitude,
                        "distance_miles": round(
                            distance_miles,
                            2,
                        ),
                    }
                )

        nearby_stations.sort(
            key=lambda station: station["distance_miles"]
        )

        return Response(
            {
                "count": len(nearby_stations),
                "radius_km": radius_km,
                "results": nearby_stations,
            }
        )

    @action(detail=False, methods=["get"])
    def route(self, request):
        start_lat = request.query_params.get("start_lat")
        start_lon = request.query_params.get("start_lon")
        finish_lat = request.query_params.get("finish_lat")
        finish_lon = request.query_params.get("finish_lon")

        if not all(
            [
                start_lat,
                start_lon,
                finish_lat,
                finish_lon,
            ]
        ):
            return Response(
                {
                    "error": (
                        "start_lat, start_lon, finish_lat, "
                        "and finish_lon are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_lat = float(start_lat)
            start_lon = float(start_lon)
            finish_lat = float(finish_lat)
            finish_lon = float(finish_lon)
        except ValueError:
            return Response(
                {
                    "error": "All coordinates must be valid numbers."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (-90 <= start_lat <= 90):
            return Response(
                {
                    "error": "start_lat must be between -90 and 90."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (-90 <= finish_lat <= 90):
            return Response(
                {
                    "error": "finish_lat must be between -90 and 90."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (-180 <= start_lon <= 180):
            return Response(
                {
                    "error": "start_lon must be between -180 and 180."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (-180 <= finish_lon <= 180):
            return Response(
                {
                    "error": "finish_lon must be between -180 and 180."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_key = config("OPENROUTESERVICE_API_KEY", default="")

        if not api_key:
            return Response(
                {
                    "error": "OpenRouteService API key is not configured."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        url = (
            "https://api.heigit.org/"
            "openrouteservice/v2/directions/"
            "driving-car/geojson"
        )

        payload = {
            "coordinates": [
                [start_lon, start_lat],
                [finish_lon, finish_lat],
            ]
        }

        try:
            route_response = requests.post(
                url,
                json=payload,
                headers={
                    "Authorization": api_key,
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            return Response(
                {
                    "error": "Routing service request failed.",
                    "details": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if route_response.status_code != 200:
            return Response(
                {
                    "error": "Routing service returned an error.",
                    "details": route_response.text[:500],
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        route_data = route_response.json()

        try:
            feature = route_data["features"][0]
            geometry = feature["geometry"]
            properties = feature["properties"]
            summary = properties["summary"]

            route_coordinates = geometry["coordinates"]

            route_distance_meters = summary["distance"]
            route_duration_seconds = summary["duration"]

        except (KeyError, IndexError, TypeError):
            return Response(
                {
                    "error": "Invalid route response from routing service."
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        route_distance_miles = route_distance_meters / 1609.344

        stations = FuelStation.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
        ).order_by("id")

        candidates = []

        for station in stations:
            station_distance_from_route = distance_to_route(
                (
                    station.latitude,
                    station.longitude,
                ),
                route_coordinates,
            )

            if station_distance_from_route <= ROUTE_CORRIDOR_MILES:
                station_route_position = haversine_distance(
                    start_lat,
                    start_lon,
                    station.latitude,
                    station.longitude,
                )

                candidates.append(
                    {
                        "station": station,
                        "distance_from_route": (
                            station_distance_from_route
                        ),
                        "route_position": station_route_position,
                    }
                )

        candidates.sort(
            key=lambda item: item["route_position"]
        )

        fuel_plan = {
            "stops": [],
            "total_fuel_gallons": round(
                route_distance_miles / FUEL_ECONOMY_MPG,
                2,
            ),
            "total_fuel_cost": 0.0,
            "stations_considered": len(candidates),
            "final_leg_miles": round(route_distance_miles, 2),
            "final_leg_gallons": round(
                route_distance_miles / FUEL_ECONOMY_MPG,
                2,
            ),
            "final_leg_cost": 0.0,
        }

        if not candidates:
            return Response(
                {
                    "route": {
                        "distance_miles": round(
                            route_distance_miles,
                            2,
                        ),
                        "duration_minutes": round(
                            route_duration_seconds / 60,
                            2,
                        ),
                        "geometry": geometry,
                    },
                    "vehicle": {
                        "max_range_miles": MAX_RANGE_MILES,
                        "fuel_economy_mpg": FUEL_ECONOMY_MPG,
                    },
                    "fuel_plan": fuel_plan,
                }
            )

        if route_distance_miles <= MAX_RANGE_MILES:
            cheapest = min(
                candidates,
                key=lambda item: float(
                    item["station"].retail_price
                ),
            )

            station = cheapest["station"]

            gallons_needed = (
                route_distance_miles / FUEL_ECONOMY_MPG
            )

            fuel_cost = (
                gallons_needed
                * float(station.retail_price)
            )

            fuel_plan["stops"] = [
                {
                    "station_id": station.id,
                    "truckstop_name": station.truckstop_name,
                    "city": station.city,
                    "state": station.state,
                    "retail_price_per_gallon": float(
                        station.retail_price
                    ),
                    "latitude": station.latitude,
                    "longitude": station.longitude,
                    "route_position_miles": round(
                        cheapest["route_position"],
                        2,
                    ),
                    "distance_from_route_miles": round(
                        cheapest["distance_from_route"],
                        2,
                    ),
                    "miles_since_previous_stop": round(
                        route_distance_miles,
                        2,
                    ),
                    "gallons_needed": round(
                        gallons_needed,
                        2,
                    ),
                    "fuel_cost": round(
                        fuel_cost,
                        2,
                    ),
                }
            ]

            fuel_plan["total_fuel_cost"] = round(
                fuel_cost,
                2,
            )

            fuel_plan["final_leg_miles"] = round(
                route_distance_miles,
                2,
            )

            fuel_plan["final_leg_gallons"] = round(
                gallons_needed,
                2,
            )

            fuel_plan["final_leg_cost"] = round(
                fuel_cost,
                2,
            )

        else:
            nodes = [
                {
                    "type": "start",
                    "station": None,
                    "position": 0.0,
                    "distance_from_route": 0.0,
                }
            ]

            for candidate in candidates:
                if (
                    0
                    < candidate["route_position"]
                    < route_distance_miles
                ):
                    nodes.append(
                        {
                            "type": "station",
                            "station": candidate["station"],
                            "position": candidate[
                                "route_position"
                            ],
                            "distance_from_route": candidate[
                                "distance_from_route"
                            ],
                        }
                    )

            nodes.append(
                {
                    "type": "finish",
                    "station": None,
                    "position": route_distance_miles,
                    "distance_from_route": 0.0,
                }
            )

            nodes.sort(
                key=lambda node: node["position"]
            )

            node_count = len(nodes)

            dp = [float("inf")] * node_count
            previous = [None] * node_count

            dp[0] = 0.0

            for i in range(node_count):
                if dp[i] == float("inf"):
                    continue

                for j in range(i + 1, node_count):
                    leg_distance = (
                        nodes[j]["position"]
                        - nodes[i]["position"]
                    )

                    if leg_distance > MAX_RANGE_MILES:
                        break

                    if nodes[j]["type"] == "finish":
                        if nodes[i]["type"] == "station":
                            price = float(
                                nodes[i]["station"].retail_price
                            )
                        else:
                            continue
                    else:
                        price = float(
                            nodes[j]["station"].retail_price
                        )

                    gallons = (
                        leg_distance
                        / FUEL_ECONOMY_MPG
                    )

                    cost = gallons * price

                    new_cost = dp[i] + cost

                    if new_cost < dp[j]:
                        dp[j] = new_cost
                        previous[j] = i

            finish_index = node_count - 1

            if dp[finish_index] == float("inf"):
                return Response(
                    {
                        "error": (
                            "No feasible fueling plan was found "
                            "within the 500-mile vehicle range."
                        ),
                        "route": {
                            "distance_miles": round(
                                route_distance_miles,
                                2,
                            ),
                            "duration_minutes": round(
                                route_duration_seconds / 60,
                                2,
                            ),
                            "geometry": geometry,
                        },
                        "vehicle": {
                            "max_range_miles": MAX_RANGE_MILES,
                            "fuel_economy_mpg": FUEL_ECONOMY_MPG,
                        },
                        "fuel_plan": fuel_plan,
                    },
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            path = []

            current = finish_index

            while current is not None:
                path.append(current)
                current = previous[current]

            path.reverse()

            selected_stations = []

            for index in path:
                if nodes[index]["type"] == "station":
                    selected_stations.append(nodes[index])

            stops = []

            previous_position = 0.0

            for station_node in selected_stations:
                station = station_node["station"]

                leg_distance = (
                    station_node["position"]
                    - previous_position
                )

                gallons_needed = (
                    leg_distance
                    / FUEL_ECONOMY_MPG
                )

                fuel_cost = (
                    gallons_needed
                    * float(station.retail_price)
                )

                stops.append(
                    {
                        "station_id": station.id,
                        "truckstop_name": station.truckstop_name,
                        "city": station.city,
                        "state": station.state,
                        "retail_price_per_gallon": float(
                            station.retail_price
                        ),
                        "latitude": station.latitude,
                        "longitude": station.longitude,
                        "route_position_miles": round(
                            station_node["position"],
                            2,
                        ),
                        "distance_from_route_miles": round(
                            station_node["distance_from_route"],
                            2,
                        ),
                        "miles_since_previous_stop": round(
                            leg_distance,
                            2,
                        ),
                        "gallons_needed": round(
                            gallons_needed,
                            2,
                        ),
                        "fuel_cost": round(
                            fuel_cost,
                            2,
                        ),
                    }
                )

                previous_position = station_node["position"]

            if selected_stations:
                last_station = selected_stations[-1]

                final_leg_miles = (
                    route_distance_miles
                    - last_station["position"]
                )

                last_station_price = float(
                    last_station["station"].retail_price
                )

                final_leg_gallons = (
                    final_leg_miles
                    / FUEL_ECONOMY_MPG
                )

                final_leg_cost = (
                    final_leg_gallons
                    * last_station_price
                )

            else:
                final_leg_miles = route_distance_miles
                final_leg_gallons = (
                    route_distance_miles
                    / FUEL_ECONOMY_MPG
                )
                final_leg_cost = 0.0

            fuel_plan["stops"] = stops
            fuel_plan["total_fuel_cost"] = round(
                dp[finish_index],
                2,
            )
            fuel_plan["final_leg_miles"] = round(
                final_leg_miles,
                2,
            )
            fuel_plan["final_leg_gallons"] = round(
                final_leg_gallons,
                2,
            )
            fuel_plan["final_leg_cost"] = round(
                final_leg_cost,
                2,
            )

        return Response(
            {
                "route": {
                    "distance_miles": round(
                        route_distance_miles,
                        2,
                    ),
                    "duration_minutes": round(
                        route_duration_seconds / 60,
                        2,
                    ),
                    "geometry": geometry,
                },
                "vehicle": {
                    "max_range_miles": MAX_RANGE_MILES,
                    "fuel_economy_mpg": FUEL_ECONOMY_MPG,
                },
                "fuel_plan": fuel_plan,
            }
        )