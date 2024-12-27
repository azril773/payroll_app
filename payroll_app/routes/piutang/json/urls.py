
from django.contrib import admin
from django.urls import path,include
from payroll_app.controllers import views
urlpatterns = [
    path("piutang_json/",views.piutang_json,name="piutang_json"),
    path("tpiutang_json/",views.tpiutang_json,name="tpiutang_json"),
    path("tbh_piutang_json/",views.tbh_piutang_json,name="tbh_piutang_json"),
    path("edit_piutang_json/",views.edit_piutang_json,name="edit_piutang_json"),
    path("delete_piutang_json/",views.delete_piutang_json,name="delete_piutang_json"),
    path("edit_potongan_json/",views.edit_potongan_json,name="edit_potongan_json"),

    path("post_piutang_json/",views.post_piutang_json,name="post_piutang_json"),

    path("detail_piutang_json/",views.detail_piutang_json,name="detail_piutang_json"),
    path("edit_detail_json/",views.edit_detail_json,name="edit_detail_json"),

    path("pelunasan_json/",views.pelunasan_json,name="pelunasan_json"),

    path("tketemu_keliru/",views.tketemu_keliru,name="tketemu_keliru"),
    

]
