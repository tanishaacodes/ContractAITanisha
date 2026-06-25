from django.urls import path
from . import views

urlpatterns = [
    path('users', views.list_users, name='list_users'),
    path('users/<uuid:user_id>/role', views.update_user_role, name='update_user_role'),
    path('users/<uuid:user_id>/status', views.toggle_user_status, name='toggle_user_status'),
    path('users/<uuid:user_id>', views.delete_user, name='delete_user'),
    path('roles', views.list_roles, name='list_roles'),
    path('roles/<str:role_id>', views.delete_role, name='delete_role'),
]
