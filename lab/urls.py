from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.lab_register, name='lab_register'),
    path('', views.lab_list, name='lab_list'),
    path('my/', views.my_lab, name='my_lab'),
    path('<int:pk>/', views.lab_detail, name='lab_detail'),
    path('<int:pk>/approve/', views.lab_approve, name='lab_approve'),
]
