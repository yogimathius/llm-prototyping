from django.urls import path
from . import views

urlpatterns = [
    path('receive-prompt/', views.receive_prompt, name='receive_prompt'),
]
