
from django.contrib import admin
from django.urls import path,include
from payroll_app.controllers import views
urlpatterns = [
    path('payroll/<int:sid>', views.payroll,name="payroll"),
]
