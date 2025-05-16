
from django.contrib import admin
from django.urls import path,include
from payroll_app.controllers import views
urlpatterns = [
    path('pegawai/<int:sid>', views.pegawai,name="pegawai"),
]
