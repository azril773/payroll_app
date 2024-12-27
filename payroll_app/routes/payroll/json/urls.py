
from django.contrib import admin
from django.urls import path,include
from payroll_app.controllers import views
urlpatterns = [
    path('payroll_json', views.payroll_json,name="payroll_json"),
    path('edit_payroll', views.edit_payroll,name="edit_payroll"),

    path('bcsv', views.bcsv,name="bcsv"),
    
    path('csvp', views.csvp,name="csvp"),

    path('batalKonfirmasi', views.batalKonfirmasi,name="batalKonfirmasi"),
    path('konfirmasi', views.konfirmasi,name="konfirmasi"),
    
    path('printC', views.printC,name="printC"),
    path('printP', views.printP,name="printP"),

]
