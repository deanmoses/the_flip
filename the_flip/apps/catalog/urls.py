from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.MachineListView.as_view(), name="machine-list"),
    path("<slug:slug>/", views.MachineDetailView.as_view(), name="machine-detail"),
]
