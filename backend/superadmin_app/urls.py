"""
URL configuration for SuperAdmin user management endpoints.
All endpoints require SuperAdmin role.
"""
from django.urls import path
from . import views

urlpatterns = [
    # User Management
    path('users/', views.list_users, name='list_users'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<str:user_id>/', views.get_user, name='get_user'),
    path('users/<str:user_id>/update/', views.update_user, name='update_user'),
    path('users/<str:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/<str:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<str:user_id>/connector-permissions/', views.update_connector_permissions, name='update_connector_permissions'),

    # Role Management
    path('roles/', views.list_roles, name='list_roles'),

    # Dashboard Stats
    path('stats/', views.get_user_stats, name='get_user_stats'),
]
