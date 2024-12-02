from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='app-ocr-dashboard'),
    path('scan/', views.ScanView.as_view(), name='app-ocr-scan'),
]