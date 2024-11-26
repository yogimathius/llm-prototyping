from django.urls import path
from .views.roles import list_roles
from .views.dialogue import ask_role, full_dialogue, stream_dialogue
from .views.history import get_conversation_history

urlpatterns = [
    path("roles/", list_roles, name="list_roles"),
    path("ask-role/", ask_role, name="ask_role"),
    path("history/", get_conversation_history, name="get_history"),
    path("full-dialogue/", full_dialogue, name="full_dialogue"),
    path("stream-dialogue/", stream_dialogue, name="stream_dialogue"),
]
