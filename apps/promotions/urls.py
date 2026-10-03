from django.urls import path
from . import views

app_name = 'promotions'

urlpatterns = [
    path('', views.promotions_list, name='list'),
    path('<slug:slug>/', views.promotion_detail, name='detail'),
]
