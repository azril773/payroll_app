from django.shortcuts import render
from payroll_app.models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate, views 
from django.contrib import messages 
from django.db import transaction
from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect
from django.db.models import Q, Avg, Max, Min, Sum, Count, F 
from django.db import connection
import re
import redis
from django.http import HttpResponse, JsonResponse
import json
from rest_framework.views import APIView
from rest_framework.response import Response
import pandas as pd
import os
redisConn = redis.Redis(host="localhost",port="6379",username='azril',password=123,decode_responses=True)

# fungsi masa kerja
def fmkerja_k(masa):    
    pl = []    
        
    for m in range(1,masa+1):
        if m % 5 == 0:
            pl.append(m+1)   
    
    if not pl:
        tunjangan = 5000*masa
    else:       
        
        mpl = max(pl)
        
        if masa not in pl:    
            if masa < mpl:
                jkelipatan = len(pl) - 1
                penambah = jkelipatan*5000
                tunjangan = (masa * 5000)+penambah
            else:
                jkelipatan = len(pl)
                penambah = jkelipatan*5000
                tunjangan = (masa * 5000)+penambah
                    
        else:
            jkelipatan = len(pl)
            penambah = jkelipatan*5000
            tunjangan = (5000*masa)+penambah
            
    data = int(tunjangan)    
    return data

def fmkerja_s(masa):
    
    tunjangan = (10000*masa)-5000
    
    data = int(tunjangan)    
    return data


# fungsi periode payroll
def pperiode(cabang):
    today = date.today()
    tahun_ini = today.year
    bulan_ini = today.month
    hari_ini = today.day
    
    if summary_rekap_gaji_db.objects.using(cabang).exists():
        sm = summary_rekap_gaji_db.objects.using(cabang).last()
        ltbayar = sm.tgl_bayar

        if ltbayar.month == 12:
            periode_gaji = 1
            tahun_gaji = int(ltbayar.year) + 1
        else:
            periode_gaji = int(ltbayar.month) + 1
            tahun_gaji = int(ltbayar.year)
    else:
        if hari_ini < 26:
            periode_gaji = bulan_ini
            
            if periode_gaji == 1:
                tahun_gaji = int(tahun_ini) - 1
            else:
                tahun_gaji = tahun_ini
        else:
            periode_gaji = int(bulan_ini) + 1            
            tahun_gaji = tahun_ini
            
    pg = periode_gaji
    tg = tahun_gaji
    
    return pg,tg      

def fmkerja_lengkap(tgl_masuk):
    
    today = date.today()
    tahun_ini = today.year
    bulan_ini = today.month
    
    tmasuk_tahun = tgl_masuk.year
    tmasuk_bulan = tgl_masuk.month
    tmasuk_hari = tgl_masuk.day
    
    if int(tmasuk_tahun != tahun_ini):
        if int(tmasuk_tahun) < int(tahun_ini):
            if int(bulan_ini) == int(tmasuk_bulan):
                if int(tmasuk_hari) < 16:
                    masa = int(tahun_ini - tmasuk_tahun)
                else:
                    masa = int((tahun_ini - tmasuk_tahun) - 1)
            else:
                if int(tmasuk_bulan) < int(bulan_ini):
                    masa = int(tahun_ini - tmasuk_tahun)
                else:
                    masa = int((tahun_ini - tmasuk_tahun) - 1)
        else:
            masa = 0
    else:
        masa = 0
    
    pl = []    
        
    for m in range(1,masa+1):
        if m % 5 == 0:
            pl.append(m+1)   
    
    if not pl:
        tunjangan = 5000*masa
    else:       
        
        mpl = max(pl)
        
        if masa not in pl:    
            if masa < mpl:
                jkelipatan = len(pl) - 1
                penambah = jkelipatan*5000
                tunjangan = (masa * 5000)+penambah
            else:
                jkelipatan = len(pl)
                penambah = jkelipatan*5000
                tunjangan = (masa * 5000)+penambah
                    
        else:
            jkelipatan = len(pl)
            penambah = jkelipatan*5000
            tunjangan = (5000*masa)+penambah
                
    data = {
        'tunjangan': int(tunjangan),
        'masa': masa
    }
     
    return data


# fungsi tahun kabisat
def fkabisat():
    
    tahun_gaji = pperiode()[1]
    periode_gaji = pperiode()[0]
    
    if periode_gaji == 2:    
        if (tahun_gaji % 400 == 0) and (tahun_gaji % 100 == 0):
            kabisat = 1
        elif (tahun_gaji % 4 == 0) and (tahun_gaji % 100 != 0):
            kabisat = 1
        else:
            kabisat = 0
    else:
        kabisat = 0        
        
    data = kabisat
    return data     

# Nama hari dan nama bulan function
def nama_hari(en_day):
    if en_day == "Monday":
        hari = "Senin"
        return hari
    elif en_day == "Tuesday":
        hari = "Selasa"
        return hari
    elif en_day == "Wednesday":
        hari = "Rabu"
        return hari
    elif en_day == "Thursday":
        hari = "Kamis"
        return hari
    elif en_day == "Friday":
        hari = "Jumat"
        return hari
    elif en_day == "Saturday":
        hari = "Sabtu"
        return hari
    elif en_day == "Sunday":
        hari = "Minggu"
        return hari


def nama_bulan(int_day):
    if int_day == 1:
        bulan = "Januari"
        return bulan
    elif int_day == 2:
        bulan = "Pebruari"
        return bulan
    elif int_day == 3:
        bulan = "Maret"
        return bulan
    elif int_day == 4:
        bulan = "April"
        return bulan
    elif int_day == 5:
        bulan = "Mei"
        return bulan
    elif int_day == 6:
        bulan = "Juni"
        return bulan
    elif int_day == 7:
        bulan = "Juli"
        return bulan
    elif int_day == 8:
        bulan = "Agustus"
        return bulan
    elif int_day == 9:
        bulan = "September"
        return bulan
    elif int_day == 10:
        bulan = "Oktober"
        return bulan
    elif int_day == 11:
        bulan = "Nopember"
        return bulan
    elif int_day == 12:
        bulan = "Desember"
        return bulan


def terbilang(bil):
    angka = [
        "",
        "Satu",
        "Dua",
        "Tiga",
        "Empat",
        "Lima",
        "Enam",
        "Tujuh",
        "Delapan",
        "Sembilan",
        "Sepuluh",
        "Sebelas",
    ]
    Hasil = " "
    n = int(bil)
    if n >= 0 and n <= 11:
        Hasil = angka[n]
    elif n < 20:
        Hasil = terbilang(n - 10) + " Belas "
    elif n < 100:
        Hasil = terbilang(n / 10) + " Puluh " + terbilang(n % 10)
    elif n < 200:
        Hasil = " Seratus " + terbilang(n - 100)
    elif n < 1000:
        Hasil = terbilang(n / 100) + " Ratus " + terbilang(n % 100)
    elif n < 2000:
        Hasil = " Seribu " + terbilang(n - 1000)
    elif n < 1000000:
        Hasil = terbilang(n / 1000) + " Ribu " + terbilang(n % 1000)
    elif n < 1000000000:
        Hasil = terbilang(n / 1000000) + " Juta " + terbilang(n % 1000000)
    elif n < 1000000000000:
        Hasil = terbilang(n / 1000000000) + " Milyar " + terbilang(n % 1000000000)
    elif n < 1000000000000000:
        Hasil = (
            terbilang(n / 1000000000000) + " Triliyun " + terbilang(n % 1000000000000)
        )
    elif n == 1000000000000000:
        Hasil = "Satu Kuadriliun"
    else:
        Hasil = ":("

    return Hasil


# pecahan
def pecahan(uang):

    list_pecahan = [100000, 50000, 20000, 10000, 5000, 2000, 1000, 500, 100, 50]
    sisa = []

    seratus_ribu = []
    limapuluh_ribu = []
    duapuluh_ribu = []
    sepuluh_ribu = []
    lima_ribu = []
    dua_ribu = []
    seribu = []
    lima_ratus = []
    seratus = []
    lima_puluh = []

    uang_pecahan = []

    for pecahan in list_pecahan:

        if not sisa:
            if uang < pecahan:
                continue

            if pecahan == 100000:
                seratus_ribu.append(uang//pecahan)
                sisa.append(uang % pecahan)
            else:
                seratus_ribu.append(0)

            if pecahan == 50000:
                limapuluh_ribu.append(uang//pecahan)
                sisa.append(uang % pecahan)
            else:
                limapuluh_ribu.append(0)

            if pecahan == 20000:
                duapuluh_ribu.append(uang//pecahan)
                sisa.append(uang % pecahan)
            else:
                duapuluh_ribu.append(0)

            if pecahan == 10000:
                sepuluh_ribu.append(uang//pecahan)
                sisa.append(uang % pecahan)
            else:
                sepuluh_ribu.append(0)

            if pecahan == 5000:
                lima_ribu.append(uang//pecahan)
                sisa.append(uang % pecahan)
            else:
                lima_ribu.append(0)

            if pecahan == 2000:
                dua_ribu.append(uang//pecahan)
                sisa.append(uang % pecahan)
            else:
                dua_ribu.append(0)

            if pecahan == 1000:
                seribu.append(uang//pecahan)
                sisa.append(uang % pecahan)
            else:
                seribu.append(0)

            if pecahan == 500:
                lima_ratus.append(uang//pecahan)
                sisa.append(uang % pecahan)
            else:
                lima_ratus.append(0)

            if pecahan == 100:
                seratus.append(uang//pecahan)
                sisa.append(uang % pecahan)
            else:
                seratus.append(0)

            if pecahan == 50:
                lima_puluh.append(uang//pecahan)
                sisa.append(uang % pecahan)
            else:
                lima_puluh.append(0)

        else:
            if sisa[0] < pecahan:
                continue

            if pecahan == 100000:
                seratus_ribu.append(sisa[0]//pecahan)
                sisanya = sisa[0]
                sisa.clear()
                sisa.append(sisanya % pecahan)
            else:
                seratus_ribu.append(0)

            if pecahan == 50000:
                limapuluh_ribu.append(sisa[0]//pecahan)
                sisanya = sisa[0]
                sisa.clear()
                sisa.append(sisanya % pecahan)
            else:
                limapuluh_ribu.append(0)

            if pecahan == 20000:
                duapuluh_ribu.append(sisa[0]//pecahan)
                sisanya = sisa[0]
                sisa.clear()
                sisa.append(sisanya % pecahan)
            else:
                duapuluh_ribu.append(0)

            if pecahan == 10000:
                sepuluh_ribu.append(sisa[0]//pecahan)
                sisanya = sisa[0]
                sisa.clear()
                sisa.append(sisanya % pecahan)
            else:
                sepuluh_ribu.append(0)

            if pecahan == 5000:
                lima_ribu.append(sisa[0]//pecahan)
                sisanya = sisa[0]
                sisa.clear()
                sisa.append(sisanya % pecahan)
            else:
                lima_ribu.append(0)

            if pecahan == 2000:
                dua_ribu.append(sisa[0]//pecahan)
                sisanya = sisa[0]
                sisa.clear()
                sisa.append(sisanya % pecahan)
            else:
                dua_ribu.append(0)

            if pecahan == 1000:
                seribu.append(sisa[0]//pecahan)
                sisanya = sisa[0]
                sisa.clear()
                sisa.append(sisanya % pecahan)
            else:
                seribu.append(0)

            if pecahan == 500:
                lima_ratus.append(sisa[0]//pecahan)
                sisanya = sisa[0]
                sisa.clear()
                sisa.append(sisanya % pecahan)
            else:
                lima_ratus.append(0)

            if pecahan == 100:
                seratus.append(sisa[0]//pecahan)
                sisanya = sisa[0]
                sisa.clear()
                sisa.append(sisanya % pecahan)
            else:
                seratus.append(0)

            if pecahan == 50:
                lima_puluh.append(sisa[0]//pecahan)
                sisanya = sisa[0]
                sisa.clear()
                sisa.append(sisanya % pecahan)
            else:
                lima_puluh.append(0)

    for p in list_pecahan:
        if p == 100000:
            data = {
                'jumlah': p,
                'qty': sum(seratus_ribu)
                }
            uang_pecahan.append(data)
        elif p == 50000:
            data = {
                'jumlah': p,
                'qty': sum(limapuluh_ribu)
                }
            uang_pecahan.append(data)
        elif p == 20000:
            data = {
                'jumlah': p,
                'qty': sum(duapuluh_ribu)
                }
            uang_pecahan.append(data)
        elif p == 10000:
            data = {
                'jumlah': p,
                'qty': sum(sepuluh_ribu)
                }
            uang_pecahan.append(data)
        elif p == 5000:
            data = {
                'jumlah': p,
                'qty': sum(lima_ribu)
                }
            uang_pecahan.append(data)
        elif p == 2000:
            data = {
                'jumlah': p,
                'qty': sum(dua_ribu)
                }
            uang_pecahan.append(data)
        elif p == 1000:
            data = {
                'jumlah': p,
                'qty': sum(seribu)
                }
            uang_pecahan.append(data)
        elif p == 500:
            data = {
                'jumlah': p,
                'qty': sum(lima_ratus)
                }
            uang_pecahan.append(data)
        elif p == 100:
            data = {
                'jumlah': p,
                'qty': sum(seratus)
                }
            uang_pecahan.append(data)
        elif p == 50:
            data = {
                'jumlah': p,
                'qty': sum(lima_puluh)
                }
            uang_pecahan.append(data)

    return uang_pecahan


def setRedisTransaksi(cabang,idp):
    data = []
    transaksi = transaksi_db.objects.select_related("pegawai","jenis_transaksi","kode_piutang").using(cabang).filter(pegawai_id=int(idp))
    # Jika belum ambil semua data dari table transaksi
    for trans in transaksi:
        obj = {
            "id":trans.pk,
            "tgl":str(trans.tgl),
            "pegawai":trans.pegawai.nama,
            "pegawai_id":trans.pegawai_id,
            "nilai":trans.nilai,
            "jenis_transaksi":trans.jenis_transaksi.jenis_transaksi,
            "jenis_id":trans.jenis_transaksi_id,
            "nodok":trans.nodok,
            "kode_piutang":""
        }
        data.append(obj)
    # Set redis untuk data dari transaksi
    redisConn.hset(f"transaksi-{idp}",mapping={
        "data":json.dumps(data)
    })
    # Set expire data selama 5 menit
    redisConn.expire(f"transaksi-{idp}",300)


def authorization(roles):
    def view(func):
        def process(r,*args, **kwargs):
            try:
                user = r.session["user"]
                print(user)
                akses = akses_db.objects.filter(user_id=user["id"]).last()
                print(akses)
                if not akses:
                    messages.error(r,"Akses anda belum ditentukan")
                    return redirect("beranda")
                
                if not "*" in roles:
                    if not akses.akses in roles:
                        messages.error(r,"Anda tidak memiliki akses")
                        return redirect("beranda")
                    
                res = func(r,*args, **kwargs)
                return res
            except Exception as e:
                print(e)
                messages.error(r,"Silahkan login terlebih dahulu")
                return redirect("beranda")
        return process
    return view

# def objpayroll(id,gaji,pot,pot_rp,pot_hr,bpjs,tk,ks,ntmk,insentif,tj,tt,ket,thp,gaji_cm,rek):
#     obj = {
#         "id": id,
#         "gaji": gaji,
#         "pot": pot, # janga lupa, tanya...
#         "pot_rp": ,
#         "pot_hr": 0,
#         "bpjs": bpjs,
#         "tk": p.tk_premi,
#         "ks": p.ks_premi,
#         "ntmk": 0,
#         "jinsentif": 0,
#         "tj": 0,
#         "tt": 0,
#         "ket": ket,
#         "dthp": 0,
#         "gaji_cm": 0,
#         "rek": p.rek_sd_id,
#     }