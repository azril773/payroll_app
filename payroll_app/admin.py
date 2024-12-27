from django.contrib import admin
# from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import *


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login') # Added last_login
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin) 


@admin.register(akses_cabang_db)
class akses_cabang(admin.ModelAdmin):
    lsit_display = ("cabang","user")

@admin.register(akses_db)
class akses(admin.ModelAdmin):
    list_display = ("akses",)