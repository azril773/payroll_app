from django.http import HttpResponse, JsonResponse
from payroll_app.models import akses_cabang_db
from django.shortcuts import render, redirect
from django.contrib import messages 
def authentication(get_response):
    # One-time configuration and initialization.

    def auth(r,*args, **kwargs):
        # Code to be executed for each r before
        # the view (and later auth) are called.
        if r.path.startswith("/app/"):
            try:
                if not r.session["user"] or not r.session["cabang"] or not r.session["ccabang"]:
                    messages.error(r,"Silahkan login terlebih dahulu")
                    return redirect("beranda")
                user = r.session["user"]
                cabang = r.session["ccabang"]
                ac = akses_cabang_db.objects.filter(user_id=user["id"],cabang__cabang=cabang).exists()
                if not ac:
                    messages.error(r,"Anda tidak memiliki akses ke cabang tersebut")
                    return redirect("beranda")
            except Exception as e:
                print(e)
                return redirect("beranda")

        response = get_response(r,*args, **kwargs)

        # Code to be executed for each request/response after
        # the view is called.
        return response

    return auth

