from django.urls import path
from . import views

app_name = 'sportsbook'

urlpatterns = [
    path('', views.homepage, name='home'),
    path('sport/<slug:sport_slug>/', views.sport_detail, name='sport_detail'),
    path('event/<int:event_id>/<slug:slug>/', views.event_detail, name='event_detail'),
    path('live/', views.live_events, name='live'),
]
