from django.contrib import admin
from django.urls import include, path
from store import views

urlpatterns = [
    path("saml/",                           include("saml_auth.urls")),
    path("api/records/<str:reference>",     views.api_record),
    path("records/<str:reference>",         views.records),
    path("results",                         views.results, name="results"),
    path("",                                views.home, name="home"),
]
