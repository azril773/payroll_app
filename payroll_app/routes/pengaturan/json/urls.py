from django.contrib import admin
from django.urls import path,include
from payroll_app.controllers import views
urlpatterns = [
    path('pot_absensi_json', views.pot_absensi_json,name="pot_absensi_json"),
    path('edit_pot_json', views.edit_pot_json,name="edit_pot_json"),
    path('tambah_pot_json', views.tambah_pot_json,name="tambah_pot_json"),


    path('rek_sumber_dana_json', views.rek_sumber_dana_json,name="rek_sumber_dana_json"),
    path('tambah_rek_sumber_dana_json', views.tambah_rek_sumber_dana_json,name="tambah_rek_sumber_dana_json"),
    path('edit_rek_sumber_dana_json', views.edit_rek_sumber_dana_json,name="edit_rek_sumber_dana_json"),
    path('delete_rek_sumber_dana_json', views.delete_rek_sumber_dana_json,name="delete_rek_sumber_dana_json"),


    path('ttrans_json', views.ttrans_json,name="ttrans_json"),
    path('tambah_ttrans_json', views.tambah_ttrans_json,name="tambah_ttrans_json"),
    path('edit_ttrans_json', views.edit_ttrans_json,name="edit_ttrans_json"),
    path('delete_ttrans_json', views.delete_ttrans_json,name="delete_ttrans_json"),

]
