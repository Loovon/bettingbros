from django.urls import path
from . import views

app_name = 'casino'

urlpatterns = [
    path('', views.casino_home, name='home'),
    path('category/<slug:category_slug>/', views.category_view, name='category'),
    path('game/<int:game_id>/<slug:slug>/', views.game_detail, name='game_detail'),
    path('search/', views.game_search, name='search'),
]
