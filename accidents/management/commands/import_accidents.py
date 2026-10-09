import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from accidents.models import Accident


class Command(BaseCommand):
    help = "Import road accident data from CSV"

    def handle(self, *args, **kwargs):

        csv_file = "indian_roads_dataset.csv"

        self.stdout.write("Starting import...")

        accidents = []

        with open(csv_file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:

                festival = row["festival"].strip()

                accident = Accident(
                    accident_id=int(row["accident_id"]),
                    city=row["city"],
                    state=row["state"],

                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),

                    date=datetime.strptime(
                        row["date"], "%d-%m-%Y"
                    ).date(),

                    time=datetime.strptime(
                        row["time"], "%H:%M"
                    ).time(),

                    hour=int(row["hour"]),
                    day_of_week=row["day_of_week"],
                    is_weekend=bool(int(row["is_weekend"])),

                    road_type=row["road_type"],
                    lanes=int(row["lanes"]),
                    traffic_signal=bool(int(row["traffic_signal"])),

                    weather=row["weather"],
                    visibility=row["visibility"],
                    temperature=float(row["temperature"]),

                    traffic_density=row["traffic_density"],
                    cause=row["cause"],
                    accident_severity=row["accident_severity"],

                    vehicles_involved=int(row["vehicles_involved"]),
                    casualties=int(row["casualties"]),

                    is_peak_hour=bool(int(row["is_peak_hour"])),

                    festival=festival if festival else None,

                    risk_score=float(row["risk_score"]),
                )

                accidents.append(accident)

        self.stdout.write(
            f"Loaded {len(accidents)} records."
        )

        Accident.objects.bulk_create(
            accidents,
            batch_size=1000
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(accidents)} accidents!"
            )
        )