# tracker/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/activity/', views.get_recent_activity, name='get_activity'),
    path('api/start/', views.start_tracking, name='start_tracking'),
    path('api/stop/', views.stop_tracking, name='stop_tracking'),
    path('api/stats/', views.statistics, name='statistics'),
<<<<<<< HEAD
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
=======
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52
]