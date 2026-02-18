"""Showcase URL configuration.

All routes are self-contained in this file. The root urls.py includes them
under /visit/. To remove the showcase, delete the include() line and remove
the app from INSTALLED_APPS.
"""

from django.urls import path

from flipfix.apps.showcase.views.logs import (
    ShowcaseLogEntriesView,
    ShowcaseLogsView,
    ShowcaseLogView,
)
from flipfix.apps.showcase.views.machines import (
    ShowcaseMachineEntriesView,
    ShowcaseMachinesView,
    ShowcaseMachineView,
)
from flipfix.apps.showcase.views.problems import (
    ShowcaseProblemEntriesView,
    ShowcaseProblemsView,
    ShowcaseProblemView,
)

app_name = "showcase"

urlpatterns = [
    # Machine list (showcase landing page)
    path("", ShowcaseMachinesView.as_view(), name="machines"),
    # Machine activity feed
    path(
        "machines/<slug:slug>/",
        ShowcaseMachineView.as_view(),
        name="machine",
    ),
    path(
        "machines/<slug:slug>/entries/",
        ShowcaseMachineEntriesView.as_view(),
        name="machine-entries",
    ),
    # Problem board + detail
    path("problems/", ShowcaseProblemsView.as_view(), name="problems"),
    path(
        "problems/<int:pk>/",
        ShowcaseProblemView.as_view(),
        name="problem",
    ),
    path(
        "problems/<int:pk>/log-entries/",
        ShowcaseProblemEntriesView.as_view(),
        name="problem-entries",
    ),
    # Log list + detail
    path("logs/", ShowcaseLogsView.as_view(), name="logs"),
    path(
        "logs/entries/",
        ShowcaseLogEntriesView.as_view(),
        name="log-entries",
    ),
    path("logs/<int:pk>/", ShowcaseLogView.as_view(), name="log"),
]
