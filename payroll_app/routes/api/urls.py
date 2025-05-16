
from django.contrib import admin
from django.urls import path,include
from payroll_app.controllers import views
urlpatterns = [
    path('api/update-ijin', views.ApiIjin.as_view(),name="api-update-ijin"),
]
