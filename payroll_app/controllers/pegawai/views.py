from ..lib import *

@authorization(["root","it"])
def pegawai(r,sid):
    iduser = r.session["user"]["id"]
    statusall = status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').all()
    status = status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').filter(status_pegawai_id=int(sid))
    if not status.exists():
        messages.error(r,"Status tidak terdaftar")
        return redirect("beranda")
    pegawai = pegawai_db.objects.using(r.session["ccabang"]).filter(status_id=status[0].status_pegawai.pk)
    
    divid = [p.divisi_id for p in pegawai_db.objects.using(r.session["ccabang"]).filter(status_id=status[0].status_pegawai.pk).distinct("divisi_id")]
    divisi = divisi_db.objects.using(r.session["ccabang"]).filter(pk__in=divid)
    data = {
        'status':statusall,
        "pegawai":pegawai,
        "staff":r.session["user"]["admin"],
        "divisi":divisi,
        "sid":sid,
        "status_pegawai":status[0].status_pegawai.status
    }
    return render(r,'pegawai/pegawai.html',data)

@authorization(["root","it"])
def pegawai_json(r):
    print(r.headers)
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        sid = r.POST.get("sid")
        status = status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').filter(status_pegawai_id=int(sid))
        if not status.exists():
            # messages.error(r,"Status tidak terdaftar")
            # return redirect("beranda")
            return JsonResponse({"status":"error","msg":"Status tidak terdaftar"},status=400)
        pegawai = pegawai_db.objects.using(r.session["ccabang"]).filter(status_id=status[0].status_pegawai.pk,payroll_by__iregex=r"hrd")
        data = []
        for p in pegawai:
            if p.status is None:
                continue

            if p.divisi is None:
                continue
            obj = {
                'id':p.pk,
                'nama':p.nama,
                'nik':p.nik,
                'divisi':p.divisi.divisi,
                'tgl_masuk':p.tgl_masuk if p.tgl_masuk is not None else "-",
                'gaji':p.gaji if p.gaji is not None else 0,
                'rek_dana':p.rek_sd.atas_nama if p.rek_sd is not None else "",
                'tc':p.t_c if p.t_c is not None else 0,
                'no_rekening':p.no_rekening if p.no_rekening is not None else 0,
                'tk_premi':p.tk_premi if p.tk_premi is not None else 0,
                'ks_premi':p.ks_premi if p.ks_premi is not None else 0,
                'status':p.status.status if p.status is not None else 0,
                'status_payroll':p.status_payroll if p.status_payroll is not None else 0
            }
            data.append(obj)
        return JsonResponse({"status":"success","msg":"Berhasil ambil data pegawai",'data':data},status=200)




@authorization(["root","it"])
def edit_json(r):
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        idp = r.POST.get("pegawai")
        gaji = r.POST.get("gaji")
        status = r.POST.get("status")
        tc = r.POST.get("tc")
        if idp is None or gaji is None or status is None or tc is None:
            return JsonResponse(({'status':"error","msg":"Harap isi form dengan lengkap"}),status=400)
        status_p = [s.status_pegawai.pk for s in status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').all()]

        if not pegawai_db.objects.using(r.session["ccabang"]).filter(pk=int(idp),status_id__in=status_p).exists():
            return JsonResponse({"status":"error","msg":"Pegawai tidak ada"},status=400)
        with transaction.atomic(using=r.session['ccabang']):
            try:
                    pegawai_db.objects.using(r.session["ccabang"]).filter(pk=int(idp),status_id__in=status_p).update(
                        gaji=int(gaji),
                        status_payroll=int(status),
                        t_c=tc
                    )
            except Exception as e:
                transaction.set_rollback(True,using=r.session["ccabang"])
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                return JsonResponse({"status":"error","msg":"Terjadi kesalahan"},status=500)

        return JsonResponse({"status":"success","msg":"Berhasil edit data pegawai"})

@authorization(["root","it"])
def editD_json(r):
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        divisi = r.POST.get("divisi")
        gaji = r.POST.get("gaji")
        sid = r.POST.get("sid")
        tc = r.POST.get("tc")
        status = r.POST.get("status")
        if divisi is None or gaji is None or sid is None or tc is None or status is None:
            print("KOKOKK")
            return JsonResponse({"status":"error","msg":"Harap isi form dengan lengkap"},status=500)
        status_p = [s.status_pegawai.pk for s in status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').all()]


        if not divisi_db.objects.using(r.session["ccabang"]).filter(pk=int(divisi)).exists():
            return JsonResponse({"status":"error","msg":"Divisi tidak ada"},status=400)
        with transaction.atomic(using=r.session['ccabang']):
            try:
                d = divisi_db.objects.using(r.session["ccabang"]).get(pk=int(divisi))
                for p in pegawai_db.objects.using(r.session["ccabang"]).filter(divisi_id=d.pk,status_id=int(sid)):
                    p.gaji = int(gaji)
                    p.status_payroll  = int(status)
                    p.t_c  = tc
                    p.save()
            except Exception as e:
                transaction.set_rollback(True,using=r.session["ccabang"])
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                return JsonResponse({"status":"error","msg":"Terjadi kesalahan"},status=500)

        return JsonResponse({"status":"success","msg":"Berhasil edit data pegawai"})

@authorization(["root","it"])
def editS_json(r):
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        sid = r.POST.get("sid")
        gaji = r.POST.get("gaji")
        tc = r.POST.get("tc")
        status = r.POST.get("status")
        if sid is None or gaji is None or tc is None or status is None:
            return JsonResponse({"status":"error","msg":"Harap isi form dengan lengkap"},status=400)
        if not status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').filter(status_pegawai_id=int(sid)).exists():
            return JsonResponse({"status":"error","msg":"Status tidak ada"},status=400)
        with transaction.atomic(using=r.session['ccabang']):
            try:
                s = status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').get(status_pegawai_id=int(sid))
                for p in pegawai_db.objects.using(r.session["ccabang"]).filter(status_id=s.status_pegawai.pk):
                    p.gaji = int(gaji)
                    p.status_payroll  = int(status)
                    p.t_c  = tc
                    p.save()
            except Exception as e:
                transaction.set_rollback(True,using=r.session["ccabang"])
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                return JsonResponse({"status":"error","msg":"Terjadi kesalahan"},status=500)

        return JsonResponse({"status":"success","msg":"Berhasil edit data pegawai"})
    

@authorization(["root","it"])
def editeb_json(r):
    # Memastikan bahwa request hanya dari ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        # Mengambil data dari body request
        idps = r.POST.getlist("pegawai[]")
        gaji = r.POST.get("gaji")
        tc = r.POST.get("tc")
        sp = r.POST.get("sp")
        
        # Jika data tidak lengkap maka return error
        if idps is None or gaji is None or tc is None or sp is None:
            return JsonResponse({"status":"error","msg":"Harap isi form dengan lengkap"},status=400)
        try:
            # Convert data menjadi integer
            idps = [int(idp) for idp in idps]
            gaji = int(gaji)
            failed_udpates = []

            # Ambil data pegawai dengan idps yang ada
            pegawai = pegawai_db.objects.using(r.session["ccabang"]).filter(pk__in=idps)
            # Looping pegawai yang sudah ada lalu update 
            for p in pegawai:
                try:
                    p.t_c = tc
                    p.gaji = gaji
                    p.status_payroll  = int(sp)
                    p.save(using=r.session["ccabang"])
                except Exception as e:
                    failed_udpates.append(p.pk)
            if len(failed_udpates) > 0:
                return JsonResponse({"status":"error","msg":"beberapa data gagal di update","idps":failed_udpates},status=400)
            
            return JsonResponse({'status':"success","msg":"Berhasil update data pegawai"},status=200)
        except Exception as e:
            return JsonResponse({"status":'error',"msg":"Terjadi kesalahan"},status=400)
        print(idps,tt,tj,gaji,tc,sp)
        return JsonResponse({'status':'success',"msg":"berhasil update pegawai"},status=200)