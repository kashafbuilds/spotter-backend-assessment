from rest_framework.test import APITestCase

from .models import FuelStation


class FuelStationAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        FuelStation.objects.create(
            opis_truckstop_id=1001,
            truckstop_name="Test Fuel Station",
            address="123 Main Street",
            city="Tulsa",
            state="OK",
            rack_id=1,
            retail_price=3.25,
            latitude=36.1540,
            longitude=-95.9928,
        )

        FuelStation.objects.create(
            opis_truckstop_id=1002,
            truckstop_name="Test Fuel Station 2",
            address="456 Main Street",
            city="Oklahoma City",
            state="OK",
            rack_id=2,
            retail_price=3.40,
            latitude=35.4676,
            longitude=-97.5164,
        )

    def test_fuel_stations_list(self):
        response = self.client.get("/api/fuel-stations/")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data["count"], 0)

    def test_fuel_stations_filter_by_state(self):
        response = self.client.get("/api/fuel-stations/?state=OK")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data["count"], 0)

    def test_fuel_stations_filter_by_city(self):
        response = self.client.get("/api/fuel-stations/?city=Tulsa")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data["count"], 0)

    def test_nearby_requires_coordinates(self):
        response = self.client.get("/api/fuel-stations/nearby/")
        self.assertEqual(response.status_code, 400)

    def test_nearby_with_coordinates(self):
        response = self.client.get(
            "/api/fuel-stations/nearby/",
            {
                "lat": 35.4676,
                "lon": -97.5164,
                "radius_km": 50,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_route_requires_coordinates(self):
        response = self.client.get("/api/fuel-stations/route/")
        self.assertEqual(response.status_code, 400)