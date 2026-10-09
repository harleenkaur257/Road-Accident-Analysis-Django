from django.shortcuts import render
from django.db.models import Count, Sum, Avg, Q
from django.core.paginator import Paginator
from accidents.models import Accident

# =========================
# HOME PAGE
# =========================

def home(request):
    total_accidents = Accident.objects.count()

    total_casualties = (
        Accident.objects.aggregate(total=Sum("casualties"))["total"] or 0
    )

    total_vehicles = (
        Accident.objects.aggregate(total=Sum("vehicles_involved"))["total"] or 0
    )

    average_risk = (
        Accident.objects.aggregate(avg=Avg("risk_score"))["avg"] or 0
    )

    years_covered = (
        Accident.objects.values("date__year")
        .distinct()
        .count()
    )

    total_states = (
        Accident.objects.values("state")
        .distinct()
        .count()
    )

    total_cities = (
        Accident.objects.values("city")
        .distinct()
        .count()
    )

    context = {
        "total_accidents": total_accidents,
        "total_casualties": total_casualties,
        "total_vehicles": total_vehicles,
        "average_risk": round(average_risk, 2),
        "total_columns": 24,
        "years_covered": years_covered,
        "total_states": total_states,
        "total_cities": total_cities,
    }

    return render(request, "dashboard/home.html", context)


# =========================
# ANALYSIS OPTIONS
# =========================

ANALYSIS_OPTIONS = {
    "city": [
        ("accident_count", "Accident Count"),
        ("severity", "Severity"),
        ("risk_score", "Risk Score"),
        ("casualties", "Casualties"),
        ("temperature", "Temperature"),
        ("lanes", "Lanes"),
        ("peak_hour", "Peak Hour"),
    ],

    "weather": [
        ("accident_count", "Accident Count"),
        ("severity", "Severity"),
        ("risk_score", "Risk Score"),
        ("casualties", "Casualties"),
        ("vehicles", "Vehicles"),
        ("traffic_density", "Traffic Density"),
        ("road_type", "Road Type"),
    ],

    "road": [
        ("accident_count", "Accident Count"),
        ("severity", "Severity"),
        ("risk_score", "Risk Score"),
        ("casualties", "Casualties"),
        ("vehicles", "Vehicles"),
        ("traffic_density", "Traffic Density"),
        ("weather", "Weather Impact"),
    ],

    "severity": [
        ("accident_count", "Severity Count"),
        ("percentage", "Severity Percentage"),
        ("risk_score", "Risk Score"),
        ("casualties", "Casualties"),
        ("weather", "Weather Impact"),
        ("road_type", "Road Type Impact"),
        ("vehicles", "Vehicle Impact"),
    ],

    "monthly": [
        ("accident_trend", "Accident Trend"),
        ("severity_trend", "Severity Trend"),
        ("distribution", "Monthly Distribution"),
        ("casualties", "Casualties Trend"),
        ("risk_score", "Risk Score"),
        ("weather", "Weather Impact"),
        ("year_comparison", "Year Comparison"),
    ],

    "vehicles": [
        ("accident_count", "Accident Count"),
        ("severity", "Severity"),
        ("casualties", "Casualties"),
        ("risk_score", "Risk Score"),
        ("weather", "Weather Impact"),
        ("road_type", "Road Type"),
        ("traffic_density", "Traffic Density"),
    ],
}


SECTION_NAMES = {
    "city": "City Analysis",
    "weather": "Weather Analysis",
    "road": "Road Type Analysis",
    "severity": "Severity Analysis",
    "monthly": "Monthly Analysis",
    "vehicles": "Vehicle Involvement",
}


# =========================
# HELPER FUNCTIONS
# =========================

def clean(value):
    if value is None or value == "":
        return "Unknown"
    return str(value)


def single_group(field, metric="count", limit=None, ascending=False):
    qs = Accident.objects.values(field)

    if metric == "count":
        qs = qs.annotate(value=Count("id"))

    elif metric == "sum_casualties":
        qs = qs.annotate(value=Sum("casualties"))

    elif metric == "sum_vehicles":
        qs = qs.annotate(value=Sum("vehicles_involved"))

    elif metric == "avg_risk":
        qs = qs.annotate(value=Avg("risk_score"))

    elif metric == "avg_temperature":
        qs = qs.annotate(value=Avg("temperature"))

    elif metric == "avg_lanes":
        qs = qs.annotate(value=Avg("lanes"))

    elif metric == "avg_vehicles":
        qs = qs.annotate(value=Avg("vehicles_involved"))

    rows = list(qs)

    rows.sort(
        key=lambda x: x["value"] or 0,
        reverse=not ascending
    )

    if limit:
        rows = rows[:limit]

    labels = [clean(row[field]) for row in rows]
    values = [
        round(float(row["value"] or 0), 2)
        for row in rows
    ]

    return labels, values


def grouped_series(
    group_field,
    series_field,
    metric="count",
    limit=None,
    ascending=False
):
    qs = Accident.objects.values(
        group_field,
        series_field
    )

    if metric == "count":
        qs = qs.annotate(value=Count("id"))

    elif metric == "casualties":
        qs = qs.annotate(value=Sum("casualties"))

    elif metric == "vehicles":
        qs = qs.annotate(value=Avg("vehicles_involved"))

    rows = list(qs)

    groups = {}
    series = {}

    for row in rows:
        group = row[group_field]
        serie = row[series_field]
        value = float(row["value"] or 0)

        groups[group] = clean(group)
        series[serie] = clean(serie)

    totals = {}

    for row in rows:
        group = row[group_field]
        totals[group] = totals.get(group, 0) + float(
            row["value"] or 0
        )

    group_keys = list(groups.keys())

    if ascending:
        group_keys.sort(key=lambda x: str(x))
    else:
        group_keys.sort(
            key=lambda x: totals.get(x, 0),
            reverse=True
        )

    if limit:
        group_keys = group_keys[:limit]

    series_keys = list(series.keys())
    series_keys.sort(key=lambda x: str(x))

    labels = [groups[x] for x in group_keys]

    result_series = []

    for serie in series_keys:
        values = []

        for group in group_keys:
            value = 0

            for row in rows:
                if (
                    row[group_field] == group
                    and row[series_field] == serie
                ):
                    value = float(row["value"] or 0)
                    break

            values.append(round(value, 2))

        result_series.append({
            "name": series[serie],
            "values": values,
        })

    return labels, result_series


def peak_hour_data():
    rows = list(
        Accident.objects
        .values("city")
        .annotate(
            total=Count("id"),
            peak=Count(
                "id",
                filter=Q(is_peak_hour=True)
            )
        )
    )

    rows.sort(
        key=lambda x: x["total"],
        reverse=True
    )

    rows = rows[:10]

    labels = [clean(row["city"]) for row in rows]

    values = []

    for row in rows:
        total = row["total"] or 1
        percentage = (row["peak"] / total) * 100
        values.append(round(percentage, 2))

    return labels, values


def monthly_single(metric="count"):
    if metric == "count":
        rows = list(
            Accident.objects
            .values("date__month")
            .annotate(value=Count("id"))
        )

    elif metric == "casualties":
        rows = list(
            Accident.objects
            .values("date__month")
            .annotate(value=Sum("casualties"))
        )

    elif metric == "risk":
        rows = list(
            Accident.objects
            .values("date__month")
            .annotate(value=Avg("risk_score"))
        )

    month_names = [
        "",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    rows.sort(key=lambda x: x["date__month"])

    labels = [
        month_names[row["date__month"]]
        for row in rows
    ]

    values = [
        round(float(row["value"] or 0), 2)
        for row in rows
    ]

    return labels, values


def chart_data(
    title,
    labels,
    values=None,
    series=None,
    chart_type="bar",
    stacked=False,
    y_title=""
):
    return {
        "title": title,
        "labels": labels,
        "values": values or [],
        "series": series or [],
        "type": chart_type,
        "stacked": stacked,
        "y_title": y_title,
    }


# =========================
# ANALYSIS PAGE
# =========================

def analysis(request):

    section = request.GET.get("section", "city")
    chart = request.GET.get("chart", "accident_count")

    if section not in ANALYSIS_OPTIONS:
        section = "city"

    valid_charts = [
        item[0]
        for item in ANALYSIS_OPTIONS[section]
    ]

    if chart not in valid_charts:
        chart = valid_charts[0]

    # -------------------------
    # CITY
    # -------------------------

    if section == "city":

        if chart == "accident_count":
            labels, values = single_group(
                "city",
                "count",
                10
            )

            data = chart_data(
                "Top 10 Cities by Accident Count",
                labels,
                values,
                y_title="Accidents"
            )

        elif chart == "severity":
            labels, series = grouped_series(
                "city",
                "accident_severity",
                "count",
                10
            )

            data = chart_data(
                "Accident Severity by City",
                labels,
                series=series,
                stacked=True,
                y_title="Accidents"
            )

        elif chart == "risk_score":
            labels, values = single_group(
                "city",
                "avg_risk",
                10
            )

            data = chart_data(
                "Average Risk Score by City",
                labels,
                values,
                y_title="Risk Score"
            )

        elif chart == "casualties":
            labels, values = single_group(
                "city",
                "sum_casualties",
                10
            )

            data = chart_data(
                "Casualties by City",
                labels,
                values,
                y_title="Casualties"
            )

        elif chart == "temperature":
            labels, values = single_group(
                "city",
                "avg_temperature",
                10
            )

            data = chart_data(
                "Average Temperature by City",
                labels,
                values,
                y_title="Temperature"
            )

        elif chart == "lanes":
            labels, values = single_group(
                "city",
                "avg_lanes",
                10
            )

            data = chart_data(
                "Average Lanes by City",
                labels,
                values,
                y_title="Lanes"
            )

        else:
            labels, values = peak_hour_data()

            data = chart_data(
                "Peak Hour Accident Percentage",
                labels,
                values,
                y_title="Peak Hour %"
            )


    # -------------------------
    # WEATHER
    # -------------------------

    elif section == "weather":

        if chart == "accident_count":
            labels, values = single_group(
                "weather",
                "count"
            )

            data = chart_data(
                "Accidents by Weather",
                labels,
                values,
                y_title="Accidents"
            )

        elif chart == "severity":
            labels, series = grouped_series(
                "weather",
                "accident_severity",
                "count"
            )

            data = chart_data(
                "Severity by Weather",
                labels,
                series=series,
                stacked=True
            )

        elif chart == "risk_score":
            labels, values = single_group(
                "weather",
                "avg_risk"
            )

            data = chart_data(
                "Average Risk Score by Weather",
                labels,
                values
            )

        elif chart == "casualties":
            labels, values = single_group(
                "weather",
                "sum_casualties"
            )

            data = chart_data(
                "Casualties by Weather",
                labels,
                values
            )

        elif chart == "vehicles":
            labels, values = single_group(
                "weather",
                "avg_vehicles"
            )

            data = chart_data(
                "Average Vehicles by Weather",
                labels,
                values
            )

        elif chart == "traffic_density":
            labels, series = grouped_series(
                "weather",
                "traffic_density",
                "count"
            )

            data = chart_data(
                "Traffic Density by Weather",
                labels,
                series=series,
                stacked=True
            )

        else:
            labels, series = grouped_series(
                "weather",
                "road_type",
                "count"
            )

            data = chart_data(
                "Road Type by Weather",
                labels,
                series=series,
                stacked=True
            )


    # -------------------------
    # ROAD TYPE
    # -------------------------

    elif section == "road":

        if chart == "accident_count":
            labels, values = single_group(
                "road_type",
                "count"
            )

            data = chart_data(
                "Accidents by Road Type",
                labels,
                values
            )

        elif chart == "severity":
            labels, series = grouped_series(
                "road_type",
                "accident_severity",
                "count"
            )

            data = chart_data(
                "Severity by Road Type",
                labels,
                series=series,
                stacked=True
            )

        elif chart == "risk_score":
            labels, values = single_group(
                "road_type",
                "avg_risk"
            )

            data = chart_data(
                "Average Risk Score by Road Type",
                labels,
                values
            )

        elif chart == "casualties":
            labels, values = single_group(
                "road_type",
                "sum_casualties"
            )

            data = chart_data(
                "Casualties by Road Type",
                labels,
                values
            )

        elif chart == "vehicles":
            labels, values = single_group(
                "road_type",
                "avg_vehicles"
            )

            data = chart_data(
                "Average Vehicles by Road Type",
                labels,
                values
            )

        elif chart == "traffic_density":
            labels, series = grouped_series(
                "road_type",
                "traffic_density",
                "count"
            )

            data = chart_data(
                "Traffic Density by Road Type",
                labels,
                series=series,
                stacked=True
            )

        else:
            labels, series = grouped_series(
                "road_type",
                "weather",
                "count"
            )

            data = chart_data(
                "Weather Impact by Road Type",
                labels,
                series=series,
                stacked=True
            )


    # -------------------------
    # SEVERITY
    # -------------------------

    elif section == "severity":

        if chart in ["accident_count", "percentage"]:

            labels, values = single_group(
                "accident_severity",
                "count"
            )

            if chart == "percentage":
                total = sum(values) or 1
                values = [
                    round((value / total) * 100, 2)
                    for value in values
                ]

                data = chart_data(
                    "Accident Severity Percentage",
                    labels,
                    values,
                    chart_type="pie"
                )

            else:
                data = chart_data(
                    "Accident Severity Count",
                    labels,
                    values,
                    chart_type="pie"
                )

        elif chart == "risk_score":
            labels, values = single_group(
                "accident_severity",
                "avg_risk"
            )

            data = chart_data(
                "Average Risk Score by Severity",
                labels,
                values
            )

        elif chart == "casualties":
            labels, values = single_group(
                "accident_severity",
                "sum_casualties"
            )

            data = chart_data(
                "Casualties by Severity",
                labels,
                values
            )

        elif chart == "weather":
            labels, series = grouped_series(
                "accident_severity",
                "weather",
                "count"
            )

            data = chart_data(
                "Weather Impact on Severity",
                labels,
                series=series,
                stacked=True
            )

        elif chart == "road_type":
            labels, series = grouped_series(
                "accident_severity",
                "road_type",
                "count"
            )

            data = chart_data(
                "Road Type Impact on Severity",
                labels,
                series=series,
                stacked=True
            )

        else:
            labels, values = single_group(
                "accident_severity",
                "avg_vehicles"
            )

            data = chart_data(
                "Vehicle Impact by Severity",
                labels,
                values
            )


    # -------------------------
    # MONTHLY
    # -------------------------

    elif section == "monthly":

        if chart == "accident_trend":
            labels, values = monthly_single("count")

            data = chart_data(
                "Monthly Accident Trend",
                labels,
                values,
                chart_type="line"
            )

        elif chart == "severity_trend":

            labels, series = grouped_series(
                "date__month",
                "accident_severity",
                "count",
                ascending=True
            )

            month_names = [
                "",
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]

            labels = [
                month_names[int(x)]
                for x in labels
            ]

            data = chart_data(
                "Monthly Severity Trend",
                labels,
                series=series,
                chart_type="line"
            )

        elif chart == "distribution":
            labels, values = monthly_single("count")

            data = chart_data(
                "Monthly Accident Distribution",
                labels,
                values
            )

        elif chart == "casualties":
            labels, values = monthly_single("casualties")

            data = chart_data(
                "Monthly Casualties Trend",
                labels,
                values,
                chart_type="line"
            )

        elif chart == "risk_score":
            labels, values = monthly_single("risk")

            data = chart_data(
                "Monthly Risk Score",
                labels,
                values,
                chart_type="line"
            )

        elif chart == "weather":

            labels, series = grouped_series(
                "date__month",
                "weather",
                "count",
                ascending=True
            )

            month_names = [
                "",
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]

            labels = [
                month_names[int(x)]
                for x in labels
            ]

            data = chart_data(
                "Monthly Weather Impact",
                labels,
                series=series,
                stacked=True
            )

        else:
            labels, values = single_group(
                "date__year",
                "count",
                ascending=True
            )

            data = chart_data(
                "Year Comparison",
                labels,
                values
            )


    # -------------------------
    # VEHICLES
    # -------------------------

    else:

        if chart == "accident_count":
            labels, values = single_group(
                "vehicles_involved",
                "count",
                ascending=True
            )

            data = chart_data(
                "Accidents by Vehicle Involvement",
                labels,
                values
            )

        elif chart == "severity":
            labels, series = grouped_series(
                "vehicles_involved",
                "accident_severity",
                "count",
                ascending=True
            )

            data = chart_data(
                "Severity by Vehicle Involvement",
                labels,
                series=series,
                stacked=True
            )

        elif chart == "casualties":
            labels, values = single_group(
                "vehicles_involved",
                "sum_casualties",
                ascending=True
            )

            data = chart_data(
                "Casualties by Vehicle Involvement",
                labels,
                values
            )

        elif chart == "risk_score":
            labels, values = single_group(
                "vehicles_involved",
                "avg_risk",
                ascending=True
            )

            data = chart_data(
                "Risk Score by Vehicle Involvement",
                labels,
                values
            )

        elif chart == "weather":
            labels, series = grouped_series(
                "vehicles_involved",
                "weather",
                "count",
                ascending=True
            )

            data = chart_data(
                "Weather Impact by Vehicles",
                labels,
                series=series,
                stacked=True
            )

        elif chart == "road_type":
            labels, series = grouped_series(
                "vehicles_involved",
                "road_type",
                "count",
                ascending=True
            )

            data = chart_data(
                "Road Type by Vehicles",
                labels,
                series=series,
                stacked=True
            )

        else:
            labels, series = grouped_series(
                "vehicles_involved",
                "traffic_density",
                "count",
                ascending=True
            )

            data = chart_data(
                "Traffic Density by Vehicles",
                labels,
                series=series,
                stacked=True
            )


    # =========================
    # TEMPLATE CONTEXT
    # =========================

    section_links = []

    for key, name in SECTION_NAMES.items():
        section_links.append({
            "key": key,
            "name": name,
            "first_chart": ANALYSIS_OPTIONS[key][0][0],
        })

    context = {
        "section": section,
        "section_name": SECTION_NAMES[section],
        "chart": chart,
        "chart_options": ANALYSIS_OPTIONS[section],
        "section_links": section_links,
        "chart_data": data,
    }

    return render(
        request,
        "dashboard/analysis.html",
        context
    )
# =========================
# ACCIDENT MAP
# =========================

def accident_map(request):

    selected_weather = request.GET.get("weather", "All")
    selected_city = request.GET.get("city", "All")

    weather_options = sorted(
        Accident.objects
        .values_list("weather", flat=True)
        .distinct()
    )

    city_options = sorted(
        Accident.objects
        .values_list("city", flat=True)
        .distinct()
    )

    queryset = Accident.objects.all()

    if selected_weather != "All":
        queryset = queryset.filter(
            weather=selected_weather
        )

    if selected_city != "All":
        queryset = queryset.filter(
            city=selected_city
        )

    rows = list(
        queryset.values(
            "state",
            "city",
            "latitude",
            "longitude"
        )
        .annotate(
            total_accidents=Count("id"),
            total_casualties=Sum("casualties")
        )
        .order_by("-total_accidents")
    )

    map_data = []

    for row in rows:

        if row["latitude"] is None or row["longitude"] is None:
            continue

        map_data.append({
            "state": row["state"] or "Unknown",
            "city": row["city"] or "Unknown",
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "accidents": row["total_accidents"],
            "casualties": row["total_casualties"] or 0,
        })

    context = {
        "map_data": map_data,
        "weather_options": weather_options,
        "city_options": city_options,
        "selected_weather": selected_weather,
        "selected_city": selected_city,
    }

    return render(
        request,
        "dashboard/accident_map.html",
        context
    )
# =========================
# ABOUT PAGE
# =========================

def about(request):
    return render(
        request,
        "dashboard/about.html"
    )

# =========================
# QUERY / DATA ASSISTANT
# =========================

def query(request):

    question = ""
    answer = ""
    result_type = "normal"

    if request.method == "POST":

        question = request.POST.get("question", "").strip()

        q = question.lower()

        if not question:

            answer = "Please enter a question."

        # TOTAL ACCIDENTS
        elif (
            "how many accidents" in q
            or "total accidents" in q
            or "number of accidents" in q
        ):

            total = Accident.objects.count()

            answer = (
                f"There are <strong>{total:,}</strong> "
                "accident records in the database."
            )

        # TOTAL CASUALTIES
        elif (
            "total casualties" in q
            or "how many casualties" in q
            or "number of casualties" in q
        ):

            total = (
                Accident.objects
                .aggregate(total=Sum("casualties"))
                ["total"] or 0
            )

            answer = (
                f"The total number of casualties is "
                f"<strong>{total:,}</strong>."
            )

        # TOTAL VEHICLES
        elif (
            "total vehicles" in q
            or "how many vehicles" in q
            or "vehicles involved" in q
        ):

            total = (
                Accident.objects
                .aggregate(total=Sum("vehicles_involved"))
                ["total"] or 0
            )

            answer = (
                f"The total number of vehicles involved is "
                f"<strong>{total:,}</strong>."
            )

        # AVERAGE RISK
        elif (
            "average risk" in q
            or "avg risk" in q
            or "risk score" in q
        ):

            value = (
                Accident.objects
                .aggregate(avg=Avg("risk_score"))
                ["avg"] or 0
            )

            answer = (
                f"The average accident risk score is "
                f"<strong>{value:.2f}</strong>."
            )

        # MOST ACCIDENTS CITY
        elif (
            "most accidents" in q
            and "city" in q
        ) or (
            "highest accident city" in q
        ):

            row = (
                Accident.objects
                .values("city")
                .annotate(total=Count("id"))
                .order_by("-total")
                .first()
            )

            if row:

                answer = (
                    f"<strong>{row['city']}</strong> has "
                    f"<strong>{row['total']:,}</strong> "
                    "accident records."
                )

        # MOST ACCIDENTS WEATHER
        elif (
            "weather" in q
            and (
                "most accidents" in q
                or "highest" in q
            )
        ):

            row = (
                Accident.objects
                .values("weather")
                .annotate(total=Count("id"))
                .order_by("-total")
                .first()
            )

            if row:

                answer = (
                    f"<strong>{row['weather']}</strong> has the "
                    f"highest number of accidents with "
                    f"<strong>{row['total']:,}</strong> records."
                )

        # MOST ACCIDENTS ROAD TYPE
        elif (
            "road type" in q
            and (
                "most accidents" in q
                or "highest" in q
            )
        ):

            row = (
                Accident.objects
                .values("road_type")
                .annotate(total=Count("id"))
                .order_by("-total")
                .first()
            )

            if row:

                answer = (
                    f"<strong>{row['road_type']}</strong> has the "
                    f"highest number of accidents with "
                    f"<strong>{row['total']:,}</strong> records."
                )

        # MOST COMMON SEVERITY
        elif (
            "most common severity" in q
            or "most common accident severity" in q
            or "highest severity" in q
        ):

            row = (
                Accident.objects
                .values("accident_severity")
                .annotate(total=Count("id"))
                .order_by("-total")
                .first()
            )

            if row:

                answer = (
                    f"The most common accident severity is "
                    f"<strong>{row['accident_severity']}</strong>, "
                    f"with <strong>{row['total']:,}</strong> records."
                )

        # YEAR QUERY
        elif "2022" in q or "2023" in q or "2024" in q or "2025" in q:

            year = None

            for possible_year in ["2022", "2023", "2024", "2025"]:

                if possible_year in q:
                    year = int(possible_year)
                    break

            if year:

                total = (
                    Accident.objects
                    .filter(date__year=year)
                    .count()
                )

                casualties = (
                    Accident.objects
                    .filter(date__year=year)
                    .aggregate(
                        total=Sum("casualties")
                    )["total"] or 0
                )

                answer = (
                    f"In <strong>{year}</strong>, there were "
                    f"<strong>{total:,}</strong> accident records "
                    f"and <strong>{casualties:,}</strong> casualties."
                )

        # CITY SEARCH
        elif "city" in q:

            words = q.replace("?", "").split()

            cities = (
                Accident.objects
                .values_list("city", flat=True)
                .distinct()
            )

            found_city = None

            for city in cities:

                if city and city.lower() in q:

                    found_city = city
                    break

            if found_city:

                total = (
                    Accident.objects
                    .filter(city=found_city)
                    .count()
                )

                casualties = (
                    Accident.objects
                    .filter(city=found_city)
                    .aggregate(
                        total=Sum("casualties")
                    )["total"] or 0
                )

                answer = (
                    f"<strong>{found_city}</strong> has "
                    f"<strong>{total:,}</strong> accident records "
                    f"and <strong>{casualties:,}</strong> casualties."
                )

            else:

                answer = (
                    "I couldn't identify a city in your question. "
                    "Try asking something like: "
                    "<strong>How many accidents are in Ludhiana?</strong>"
                )

        # HELP
        elif (
            "help" in q
            or "what can you ask" in q
            or "what can i ask" in q
        ):

            answer = (
                "You can ask about total accidents, casualties, "
                "vehicles, risk score, cities, weather, road types, "
                "severity and yearly accident statistics."
            )

        # UNKNOWN
        else:

            answer = (
                "I couldn't understand that question yet. "
                "Try one of the example questions below."
            )

    context = {
        "question": question,
        "answer": answer,
    }

    return render(
        request,
        "dashboard/query.html",
        context
    )

# =========================
# DATASET PAGE
# =========================

def dataset(request):

    search = request.GET.get("search", "").strip()
    selected_city = request.GET.get("city", "All")
    selected_state = request.GET.get("state", "All")
    selected_severity = request.GET.get("severity", "All")

    accidents = Accident.objects.all()

    # Search
    if search:
        accidents = accidents.filter(
            Q(city__icontains=search) |
            Q(state__icontains=search) |
            Q(road_type__icontains=search) |
            Q(weather__icontains=search) |
            Q(cause__icontains=search) |
            Q(accident_severity__icontains=search)
        )

    # City filter
    if selected_city != "All":
        accidents = accidents.filter(
            city=selected_city
        )

    # State filter
    if selected_state != "All":
        accidents = accidents.filter(
            state=selected_state
        )

    # Severity filter
    if selected_severity != "All":
        accidents = accidents.filter(
            accident_severity=selected_severity
        )

    accidents = accidents.order_by("-date", "-id")

    total_filtered = accidents.count()

    paginator = Paginator(
        accidents,
        25
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    cities = sorted(
        Accident.objects
        .values_list("city", flat=True)
        .distinct()
    )

    states = sorted(
        Accident.objects
        .values_list("state", flat=True)
        .distinct()
    )

    severities = sorted(
        Accident.objects
        .values_list("accident_severity", flat=True)
        .distinct()
    )

    context = {
        "page_obj": page_obj,
        "cities": cities,
        "states": states,
        "severities": severities,
        "search": search,
        "selected_city": selected_city,
        "selected_state": selected_state,
        "selected_severity": selected_severity,
        "total_filtered": total_filtered,
    }

    return render(
        request,
        "dashboard/dataset.html",
        context
    )

# =========================
# PROCESSING PAGE
# =========================

def processing(request):

    total_records = Accident.objects.count()

    total_states = (
        Accident.objects
        .values("state")
        .distinct()
        .count()
    )

    total_cities = (
        Accident.objects
        .values("city")
        .distinct()
        .count()
    )

    total_severities = (
        Accident.objects
        .values("accident_severity")
        .distinct()
        .count()
    )

    total_weather = (
        Accident.objects
        .values("weather")
        .distinct()
        .count()
    )

    total_road_types = (
        Accident.objects
        .values("road_type")
        .distinct()
        .count()
    )

    context = {
        "total_records": total_records,
        "total_states": total_states,
        "total_cities": total_cities,
        "total_severities": total_severities,
        "total_weather": total_weather,
        "total_road_types": total_road_types,
    }

    return render(
        request,
        "dashboard/processing.html",
        context
    )