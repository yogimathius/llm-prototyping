from django.urls import path
from . import views

urlpatterns = [
    path("ask-role/", views.ask_role, name="ask_role"),
    path("get-all-roles/", views.get_all_roles, name="get_all_roles"),
    path("get-history/", views.get_history, name="get_history"),
]
