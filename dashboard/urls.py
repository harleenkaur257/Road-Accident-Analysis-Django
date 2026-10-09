from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("analysis/", views.analysis, name="analysis"),
    path("accident-map/", views.accident_map, name="accident_map"),
    path("about/", views.about, name="about"),
    path("query/", views.query, name="query"),
    path("dataset/", views.dataset, name="dataset"),
    path("processing/", views.processing, name="processing"),
]