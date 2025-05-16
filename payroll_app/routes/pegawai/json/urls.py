
from django.contrib import admin
from django.urls import path,include
from payroll_app.controllers import views
urlpatterns = [
    path('pegawai_json', views.pegawai_json,name="pegawai_json"),
    path('edit_json', views.edit_json,name="edit_json"),
    path('editD_json', views.editD_json,name="editD_json"),
    path('editS_json', views.editS_json,name="editS_json"),
    path('editeb_json', views.editeb_json,name="editeb_json"),


]
