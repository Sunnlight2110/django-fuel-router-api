import csv
from django.core.management.base import BaseCommand
from routing.models import FuelStation


class Command(BaseCommand):
    help = "Load fuel station prices and join with city lat/long data"

    def handle(self, *args, **options):
        # Step 1: Build city+state -> (lat, lng) lookup
        city_coords = {}
        with open('data/uscities.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row['city'].strip().lower(), row['state_id'].strip().upper())
                city_coords[key] = (float(row['lat']), float(row['lng']))

        self.stdout.write(f"Loaded {len(city_coords)} city coordinates")

        # Step 2: Read fuel prices, dedupe by (truckstop_id) not needed —
        # just build FuelStation objects directly, join lat/lng per row
        stations = []
        skipped = 0

        with open('data/fuel-prices-for-be-assessment.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                city = row['City'].strip()
                state = row['State'].strip().upper()
                key = (city.lower(), state)

                coords = city_coords.get(key)
                if not coords:
                    skipped += 1
                    continue  # no match found, skip (or log for review)

                lat, lng = coords

                stations.append(FuelStation(
                    truckstop_id=int(row['OPIS Truckstop ID']),
                    name=row['Truckstop Name'].strip(),
                    address=row['Address'].strip(),
                    city=city,
                    state=state,
                    rack_id=int(row['Rack ID']),
                    price=float(row['Retail Price']),
                    latitude=lat,
                    longitude=lng,
                ))

        FuelStation.objects.bulk_create(stations, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(
            f"Loaded {len(stations)} stations. Skipped {skipped} (no coordinate match)."
        ))