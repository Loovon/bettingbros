from django.urls import path
from . import api_views

app_name = 'api_sportsbook'

urlpatterns = [
    path('sports/', api_views.SportListView.as_view(), name='sports_list'),
    path('events/', api_views.EventListView.as_view(), name='events_list'),
    path('events/<int:pk>/', api_views.EventDetailView.as_view(), name='event_detail'),
]
