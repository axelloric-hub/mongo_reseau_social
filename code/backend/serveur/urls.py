"""urls.py - Une seule route : /api/<action>/ ; le routage fin est fait par la table ACTIONS."""
from django.urls import path

from api import views

urlpatterns = [
    path("api/", views.sante),
    path("api/<str:action>", views.dispatch),
    path("api/<str:action>/", views.dispatch),
]
