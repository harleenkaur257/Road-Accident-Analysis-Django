from django.db import models


class Accident(models.Model):
    accident_id = models.IntegerField(unique=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)

    latitude = models.FloatField()
    longitude = models.FloatField()

    date = models.DateField()
    time = models.TimeField()

    hour = models.IntegerField()
    day_of_week = models.CharField(max_length=20)
    is_weekend = models.BooleanField(default=False)

    road_type = models.CharField(max_length=50)
    lanes = models.IntegerField()
    traffic_signal = models.BooleanField(default=False)

    weather = models.CharField(max_length=50)
    visibility = models.CharField(max_length=50)
    temperature = models.FloatField()

    traffic_density = models.CharField(max_length=50)
    cause = models.CharField(max_length=100)
    accident_severity = models.CharField(max_length=50)

    vehicles_involved = models.IntegerField()
    casualties = models.IntegerField()

    is_peak_hour = models.BooleanField(default=False)
    festival = models.CharField(max_length=100, null=True, blank=True)

    risk_score = models.FloatField()

    def __str__(self):
        return f"{self.accident_id} - {self.city} - {self.accident_severity}"