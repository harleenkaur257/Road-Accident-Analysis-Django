from django.contrib import admin
from .models import Accident


@admin.register(Accident)
class AccidentAdmin(admin.ModelAdmin):
    list_display = (
        'accident_id',
        'city',
        'state',
        'date',
        'road_type',
        'weather',
        'cause',
        'accident_severity',
        'vehicles_involved',
        'casualties',
        'risk_score',
    )

    list_filter = (
        'state',
        'road_type',
        'weather',
        'accident_severity',
        'is_weekend',
        'is_peak_hour',
    )

    search_fields = (
        'city',
        'state',
        'cause',
        'accident_severity',
    )