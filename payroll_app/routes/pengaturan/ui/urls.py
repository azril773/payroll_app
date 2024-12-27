from django.contrib import admin
from django.urls import path,include
from payroll_app.controllers import views
urlpatterns = [
    path('pot_absensi', views.pot_absensi,name="pot_absensi"),
    path('rek_sumber_dana', views.rek_sumber_dana,name="rek_sumber_dana"),
    path('ttrans', views.ttrans,name="ttrans"),

]
