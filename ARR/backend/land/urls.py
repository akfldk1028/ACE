"""URL configuration for land app."""
from django.urls import path
from . import views

app_name = 'land'

urlpatterns = [
    path('analyze/', views.analyze, name='analyze'),
    path('resolve/', views.resolve, name='resolve'),
    path('zones/', views.zones, name='zones'),
    path('stats/', views.stats, name='stats'),
]
