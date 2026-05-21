from django.urls import include, path
from store import views

urlpatterns = [
    path("api/records/<str:record_id>", views.api_record),
    path("records/<str:record_uuid>", views.records),
    path("results", views.results, name="results"),
    path("", views.home, name="home"),
    path("upload/<str:record_id>", views.upload),
    path("submitted/<str:record_id>", views.submitted),
    path("login", views.user_login),
    path("auth", views.auth, name="auth"),
    path("logout", views.user_logout, name="logout"),
]
