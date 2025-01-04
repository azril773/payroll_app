from django.contrib import admin
# from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import *


# class CustomUserAdmin(UserAdmin):
#     list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login') # Added last_login
# admin.site.unregister(User)
# admin.site.register(User, CustomUserAdmin) 

class MultiDBModelAdmin(admin.ModelAdmin):
    # A handy constant for the name of the alternate database.

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'other' database.
        obj.save(using=self.using)

    def delete_model(self, request, obj):
        # Tell Django to delete objects from the 'other' database
        obj.delete(using=self.using)

    def get_queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super().get_queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'other' database.
        return super().formfield_for_foreignkey(
            db_field, request, using=self.using, **kwargs
        )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'other' database.
        return super().formfield_for_manytomany(
            db_field, request, using=self.using, **kwargs
        )
    

class CirebonAdmin(MultiDBModelAdmin):
    using = "cirebon"

class TasikAdmin(MultiDBModelAdmin):
    using = "tasik"

class SumedangAdmin(MultiDBModelAdmin):
    using = "sumedang"

class CihideungAdmin(MultiDBModelAdmin):
    using = "cihideung"

class GarutAdmin(MultiDBModelAdmin):
    using = "garut"



cirebon = admin.AdminSite("cirebon")
tasik = admin.AdminSite("tasik")
sumedang = admin.AdminSite("sumedang")
cihideung = admin.AdminSite("cihideung")
garut = admin.AdminSite("garut")


cirebon.register(jenis_piutang_db,CirebonAdmin)
cirebon.register(jenis_transaksi_db,CirebonAdmin)
cirebon.register(summary_rekap_gaji_db,CirebonAdmin)


tasik.register(jenis_piutang_db,TasikAdmin)
tasik.register(User,TasikAdmin)
tasik.register(jenis_transaksi_db,TasikAdmin)
tasik.register(summary_rekap_gaji_db,TasikAdmin)
tasik.register(rekening_db,TasikAdmin)


cihideung.register(jenis_piutang_db,CihideungAdmin)
cihideung.register(jenis_transaksi_db,CihideungAdmin)
cihideung.register(summary_rekap_gaji_db,CihideungAdmin)


sumedang.register(jenis_piutang_db,SumedangAdmin)
sumedang.register(jenis_transaksi_db,SumedangAdmin)
sumedang.register(summary_rekap_gaji_db,SumedangAdmin)


garut.register(jenis_piutang_db,GarutAdmin)
garut.register(jenis_transaksi_db,GarutAdmin)
garut.register(summary_rekap_gaji_db,GarutAdmin)