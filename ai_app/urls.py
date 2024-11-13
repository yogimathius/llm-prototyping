from django.urls import path
from . import views

urlpatterns = [
    path("ask-role/", views.ask_role, name="get_roles"),
]
