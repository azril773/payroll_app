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
from payroll_app.admin import cirebon,sumedang, garut, cihideung, tasik
from django.urls import path, include
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate, views 
from payroll_app.models import *
from django.shortcuts import redirect
from django.contrib import messages
import os
import re
from django.shortcuts import render
from authlib.integrations.django_client import OAuth
oauth = OAuth()
oauth.register("oidc",client_id=os.environ.get("CLIENT_ID"), client_secret=os.environ.get("CLIENT_SECRET"), authorize_url=os.environ.get("AUTHORIZE_URL"),server_metadata_url=os.environ.get("CONFIG_URL") ,access_token_url=os.environ.get("TOKEN_URL"))


def login(r):
    return oauth.oidc.authorize_redirect(r,os.environ.get("REDIRECT_URI"))



def callback(r):
    token = oauth.oidc.authorize_access_token(r)
    r.session["token"] = token
    access = oauth.oidc.get(os.environ.get("USERINFO_URL"),token=token)
    result = access.json()

    groups = "".join(result["groups"])
    getCabang = re.findall('payroll_(cirebon|tasik|sumedang|garut|cihideung)',groups,re.IGNORECASE)
    if len(getCabang) <= 0:
        messages.error(r,"Anda tidak memiliki akses ke cabang manapun")
        return redirect("beranda")
    
    is_admin = [True if re.search("authentik Admins",groups,re.IGNORECASE) is not None else False]

    user = user_db.objects.filter(sub=result["sub"]).last()
    if not user:
        user_db(
            sub=result["sub"],
            email=result["email"],
            nama=result["name"],
            is_admin=is_admin[0]
        ).save()
        user = user_db.objects.filter(sub=result["sub"]).last()
    else:
        user.email = result["email"]
        user.nama = result["name"]
        user.is_admin = is_admin[0]
        user.save()
    
    # if is_admin[0]:
    #     akses = akses_db.objects.filter(user_id=user.pk).last()
    #     if not akses:
    #         akses_db(user_id=user.pk,akses='root').save()
    #     else:
    #         akses.akses = "root"
    #         akses.save()

    cbgs = cabang_db.objects.filter(cabang__in=getCabang)
    for c in cbgs:
        if not user_db.objects.using(c.cabang).filter(sub=result["sub"]).exists():
            user_db(
                pk=user.pk,
                sub=result["sub"],
                email=result["email"],
                nama=result["name"],
                is_admin=is_admin[0]
            ).save(using=c.cabang)
        else:
            user_db.objects.using(c.cabang).filter(sub=result["sub"]).update(email=result["email"],nama=result["name"],is_admin=is_admin[0])

        if not akses_cabang_db.objects.filter(cabang_id=c.pk,user_id=user.pk):
            akses_cabang_db(
                cabang_id=c.pk,
                add_by=result["name"],
                user_id=user.pk
            ).save()
        if is_admin[0]:
            akses = akses_db.objects.using(c.cabang).filter(user_id=user.pk).last()
            if not akses:
                akses_db(user_id=user.pk,akses='root').save(using=c.cabang)
            else:
                akses.akses = "root"
                akses.save(using=c.cabang)
    
    r.session["cabang"] = getCabang
    r.session["ccabang"] = getCabang[0]
    r.session["user"] = {
        "id":user.pk,
        "sub":user.sub,
        "email":user.email,
        "nama":user.nama,
        "admin":user.is_admin
    }
    return redirect("beranda")



def beranda(r):
    auth = False
    nama = None
    cabang = ''
    ccabang = []
    statusall = []
    try:
        if r.session["user"] and r.session["ccabang"] and r.session["cabang"]:
            user = r.session["user"]
            auth = True
            nama = user["nama"]
            cabang = r.session["cabang"]
            ccabang = r.session["ccabang"]
            statusall = status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').all()
        else:
            pass
    except:
        pass

    data = {
        "cabang":cabang,
        "ccabang":ccabang,
        "sid":0,
        'dsid':0,
        "nama":nama,
        "auth":auth,
        "status":statusall,
        "dashboard":os.environ.get("AUTHENTIK")
    }
    return render(r,"beranda/beranda.html",data)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cirebonadmin/', cirebon.urls),
    path('tasikadmin/', tasik.urls),
    path('sumedangadmin/', sumedang.urls),
    path('cihideungadmin/', cihideung.urls),
    path('garutadmin/', garut.urls),
    path("", beranda,name="beranda"),
    path('login/', login, name="login"),
    path('callback/', callback, name="callback"),
    path('app/', include("payroll_app.routes.urls")),
]
