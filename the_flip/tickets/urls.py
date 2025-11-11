from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import auth as auth_views
from .views import machines as machine_views
from .views import reports as report_views

urlpatterns = [
    path('', auth_views.home, name='home'),

    # Visitor URLs (public access)
    path('m/<slug:slug>/', machine_views.machine_public_view, name='machine_public'),
    path('p/<slug:slug>/', report_views.problem_report_create, name='problem_report_create'),

    # Global task URLs (maintainers only)
    path('tasks/', report_views.report_list, name='task_list'),
    path('tasks/<int:pk>/', report_views.report_detail, name='task_detail'),
    path('tasks/new/', report_views.task_create_todo, name='task_create_todo'),

    # Machine-scoped URLs (maintainers only)
    path('machines/', machine_views.machine_list, name='machine_list'),
    path('machines/<slug:slug>/', machine_views.machine_detail, name='machine_detail'),
    path('machines/<slug:slug>/tasks/', machine_views.machine_tasks_list, name='machine_tasks_list'),
    path('machines/<slug:slug>/tasks2/', machine_views.machine_tasks_list_v2, name='machine_tasks_list_v2'),
    path('machines/<slug:slug>/tasks/new/', machine_views.machine_task_create, name='machine_task_create'),
    path('machines/<slug:slug>/log/', machine_views.machine_log_list, name='machine_log_list'),
    path('machines/<slug:slug>/log/<int:pk>/', machine_views.machine_log_detail, name='machine_log_detail'),
    path('machines/<slug:slug>/log/new/', machine_views.machine_log_create, name='machine_log_create'),
    path('machines/<slug:slug>/qr/', machine_views.machine_qr, name='machine_qr'),

    # Auth
    path('login/', auth_views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
