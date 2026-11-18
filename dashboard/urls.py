from django.urls import path

from dashboard import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('dashboard/patient/', views.PatientDashboardView.as_view(), name='patient_dashboard'),
    path('dashboard/staff/', views.StaffDashboardView.as_view(), name='staff_dashboard'),
]
