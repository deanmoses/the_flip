from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('m/<slug:slug>/', views.machine_public_view, name='machine_public'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('new_report/', views.report_create, name='report_create'),
    path('new_report/<slug:machine_slug>/', views.report_create, name='report_create_qr'),
    path('machines/', views.machine_list, name='machine_list'),
    path('machines/<slug:slug>/', views.machine_detail, name='machine_detail'),
    path('machines/<slug:slug>/qr/', views.machine_qr, name='machine_qr'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
