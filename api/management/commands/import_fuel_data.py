
import pandas as pd
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import FuelStation


class Command(BaseCommand):
    help = "Import fuel station data from the CSV file"

    def handle(self, *args, **options):
        csv_path = settings.BASE_DIR / "data" / "fuel-prices.csv"

        df = pd.read_csv(csv_path)
        df = df.dropna(
            subset=[
                "OPIS Truckstop ID",
                "Truckstop Name",
                "City",
                "State",
                "Rack ID",
                "Retail Price",
            ]
        )

        stations = []
        for _, row in df.iterrows():
            stations.append(
                FuelStation(
                    opis_truckstop_id=int(row["OPIS Truckstop ID"]),
                    truckstop_name=str(row["Truckstop Name"]),
                    address=str(row["Address"]),
                    city=str(row["City"]),
                    state=str(row["State"]),
                    rack_id=int(row["Rack ID"]),
                    retail_price=Decimal(str(row["Retail Price"])),
                )
            )

        FuelStation.objects.all().delete()
        FuelStation.objects.bulk_create(stations, batch_size=1000)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(stations)} fuel stations."
            )
        )