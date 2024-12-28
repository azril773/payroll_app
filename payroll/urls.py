"""
URL configuration for payroll project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate, views 
from payroll_app.models import *
from django.shortcuts import redirect
from django.contrib import messages

def authlogin(r):
    username = r.POST.get("username")
    password = r.POST.get("password")
    cabang = r.POST.get("cabang")
    result = authenticate(username=username,password=password)
    if result is not None:
        id_user = result.pk
        print(cabang) 

        cabang = cabang_db.objects.filter(cabang=cabang).last()
        if cabang is None:
            messages.error(r,'Cabang tidak ada')
            return redirect("/")
        akses_cabang = akses_cabang_db.objects.filter(user_id=id_user,cabang_id=cabang.pk)
        if akses_cabang.exists():
            r.session["ccabang"] = akses_cabang[0].cabang.cabang
            r.session["cabang"] = [ac.cabang.cabang for ac in akses_cabang]
            login(r,result)
            print("OK")
            return redirect("setup")
        else:
            messages.error(r,'Akses cabang anda belum ditentukan')
            return redirect("/")
    else:
        messages.error(r,'Username atau password salah')
        return redirect("/")



urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path('login/', authlogin, name="next"),
    path('app/', include("payroll_app.routes.urls")),
]
