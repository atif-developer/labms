from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/register/', views.register_customer, name='register_customer'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/users/', views.user_list, name='user_list'),
    path('accounts/users/create/', views.create_user, name='create_user'),
    path('accounts/users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
]
