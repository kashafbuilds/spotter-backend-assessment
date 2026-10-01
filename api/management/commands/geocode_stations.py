from django.core.management.base import BaseCommand
from decouple import config
import openrouteservice

from api.models import FuelStation


class Command(BaseCommand):
    help = "Geocode unique fuel station locations using OpenRouteService"

    def handle(self, *args, **options):
        api_key = config("OPENROUTESERVICE_API_KEY")

        client = openrouteservice.Client(key=api_key)

        stations = FuelStation.objects.filter(
            latitude__isnull=True,
            longitude__isnull=True
        )

        locations = {}

        for station in stations:
            city = station.city.strip()
            state = station.state.strip()
            key = (city, state)

            if key not in locations:
                locations[key] = []

            locations[key].append(station.id)

        total_locations = len(locations)

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {stations.count()} stations across "
                f"{total_locations} unique city/state locations."
            )
        )

        processed = 0

        for (city, state), station_ids in locations.items():
            try:
                location = f"{city}, {state}, USA"

                result = client.pelias_search(
                    text=location,
                    size=1
                )

                features = result.get("features", [])

                if not features:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Could not geocode: {location}"
                        )
                    )
                    continue

                coordinates = features[0]["geometry"]["coordinates"]

                longitude = coordinates[0]
                latitude = coordinates[1]

                FuelStation.objects.filter(
                    id__in=station_ids
                ).update(
                    latitude=latitude,
                    longitude=longitude
                )

                processed += 1

                self.stdout.write(
                    f"Geocoded: {location} "
                    f"({len(station_ids)} stations)"
                )

            except Exception as error:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error for {location}: {error}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Successfully geocoded "
                f"{processed}/{total_locations} locations."
            )
        )