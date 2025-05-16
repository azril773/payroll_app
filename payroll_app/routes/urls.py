
from django.contrib import admin
from django.urls import path,include
from payroll_app.controllers import views
urlpatterns = [
    path('setup', views.setup,name="setup"),
    path('logout', views.user_logout, name='logout'),
    path('', include("payroll_app.routes.payroll.ui.urls")),
    path("",include("payroll_app.routes.payroll.json.urls")),
    path('', include("payroll_app.routes.pegawai.ui.urls")),
    path("",include("payroll_app.routes.pegawai.json.urls")),
    path("",include("payroll_app.routes.piutang.ui.urls")),
    path("",include("payroll_app.routes.piutang.json.urls")),
    path("",include("payroll_app.routes.api.urls")),
    path("",include("payroll_app.routes.pengaturan.json.urls")),
    path("",include("payroll_app.routes.pengaturan.ui.urls")),
]
