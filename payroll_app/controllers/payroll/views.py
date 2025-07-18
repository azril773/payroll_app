from ..lib import *
# Create your views here.
@login_required
def payroll(r,sid):
    iduser = r.user.id
    if akses_db.objects.filter(user_id=int(iduser)).exists():
        akses = akses_db.objects.get(user_id=int(iduser))
        if akses.akses == "root" or  akses.akses == "it":
            last = summary_rekap_gaji_db.objects.using(r.session["ccabang"]).last()
            if last is None:
                messages.error(r,"Rekap Gaji terakhir tidak ada")
                return redirect("beranda")
            if last.tgl_bayar.month == 12:
                bulan = 1
            else:
                bulan = last.tgl_bayar.month + 1
            status_payroll = status_pegawai_payroll_db.objects.using(f"p{r.session['ccabang']}").all()

            gaji = gaji_db.objects.using(r.session["ccabang"]).filter(status=1,status_pegawai_id=sid)
            if len(gaji) <= 0:
                modal = False
            else:
                modal = True

            data = {
                "status":status_payroll,
                "staff":r.user.is_staff,
                "sid":sid,
                'modal':modal,
                "gaji":gaji,
                "periode":nama_bulan(bulan)
            }
            return render(r,"payroll/payroll.html",data)
        else:
            messages.error(r,"Anda tidak memiliki akses ke halaman tersebut")
            return redirect("beranda")
    else:
        messages.error(r,"Data akses anda tidak ditemukan")
        return redirect("beranda")

@login_required
def payroll_json(r):
    status = r.POST.get("status")

    cabang = r.session["ccabang"]
    username = r.user.username
    today = date.today()
    hari_ini = today.day
    bulan_ini = today.month
    tahun_ini = today.year
    if not status_pegawai_payroll_db.objects.using(f'p{cabang}').filter(status_pegawai_id=int(status)).exists():
        print("OK")
        return JsonResponse({"status":"error","msg":"Status tidak terdaftar"},status=400)
    sm = summary_rekap_gaji_db.objects.using(r.session["ccabang"]).filter(status_pegawai_id=int(status)).last()
    if  sm is None:
        return JsonResponse({"status":"error","msg":"Gaji terakhir tidak ada"},status=400)
    sm = sm.tgl_bayar
    if sm.month == 12:
        bulan = 1
        tahun = int(sm.year) + 1
    else:
        bulan = int(sm.month) + 1
        tahun = int(sm.year)

    b_31 = [1,3,5,7,10,10,12]

    if int(tahun) % 400 == 0 and int(tahun) % 100 == 0:
        kabisat = 1
    elif int(tahun) % 4 == 0 and int(tahun) % 100 != 0:
        kabisat = 1
    else:
        kabisat = 0

    if int(bulan) == 2:
        if kabisat == 0:
            ftgl = f"{tahun}-{bulan}-28"
        else:
            ftgl = f"{tahun}-{bulan}-29"
    else:
        if int(bulan) in b_31:
            ftgl = f"{tahun}-{bulan}-31"
        else:
            ftgl = f"{tahun}-{bulan}-30"
        

    if bulan_ini == 1:
        periode_lalu = 12
        tahun_lalu = int(tahun_ini) - 1
    else:
        periode_lalu = int(bulan_ini) - 1
        tahun_lalu = int(tahun_ini)

    ftgl_periode_dari = f"{tahun_lalu}-{periode_lalu}-26"
    ftgl_periode_sampai = f"{tahun}-{bulan}-25"
    tdari = datetime.strptime(ftgl_periode_dari,"%Y-%m-%d")
    tsampai = datetime.strptime(ftgl_periode_sampai,"%Y-%m-%d")

    selisih_hari = tsampai - tdari
    banyak_hari = int(selisih_hari.days) + 1

    if banyak_hari <= 30:
        pembagi = 25
    else:
        pembagi = 26


    ttrans = ttrans_db.objects.using(r.session["ccabang"]).filter(jenis_transfer__iregex=r"payroll").last()
    if ttrans is not None:
        if ttrans.tanggal_transfer.month == tsampai.month and ttrans.tanggal_transfer.year == tsampai.year and ttrans.tanggal_transfer.day > tsampai.day:
            tgl_transfer = ttrans.tanggal_transfer
        else:
            tgl_transfer = datetime.strptime(f'{ftgl}',"%Y-%m-%d")  
    else:
        tgl_transfer = datetime.strptime(f'{ftgl}',"%Y-%m-%d")  
    
    potongan = pot_absensi_db.objects.using(r.session["ccabang"]).last()
    
    dijin = []
    ijin_nik = []

    if potongan is None:
        return JsonResponse({"status":"erorr","msg":"Potongan absensi tidak ada"},status=400)
    for k in data_ijin_db.objects.using(r.session["ccabang"]).filter(tahun=tahun,periode=bulan):
        data_k = {
            "idp":k.pegawai_id,
            "sb":k.sb,
            "sdl":k.sdl,
            "sdp":k.sdp,
            "ijin":k.ijin,
            "af":k.af,
            "insentif":k.insentif,
            "ket":k.ket
        }
        dijin.append(data_k)
        
    datarg = []
    for p in pegawai_db.objects.using(r.session["ccabang"]).filter(status_id=int(status),status_payroll=1,payroll_by__iregex=r'hrd'):
        if p.masa_kerja is not None:
            if p.masa_kerja > 0:
                # sesuaikan dengan cabang lain
                # if re.match("/(?i)satpam/",p.divisi.divisi):
                #     ntmk = fmkerja_s(p.masa_kerja)
                # else:
                ntmk = fmkerja_k(p.masa_kerja)
            
            else:
                ntmk = 0
        else:
            ntmk = 0
        # define piutang
        # define total hari kerja
        # jan lupa untuk kasih using sesuai dengan cabang ahrisnya    
        if rekap_db.objects.using(f'p{cabang}').filter(periode=bulan,tahun=tahun,pegawai__userid=int(p.userid)).exists():
            r = rekap_db.objects.using(f'p{cabang}').get(periode=bulan,tahun=tahun,pegawai__userid=int(p.userid))
            thk = r.tharikerja
            cm = r.cm
        else:
            thk = banyak_hari
            cm = 0
        histori_last = histori_rekap_gaji_db.objects.using(cabang).filter(pegawai_id=int(p.pk)).last()
        if histori_last is not None:
            cm_ke = histori_last.cm_ke
        else:
            cm_ke = 0
        if p.gaji is None:
            return JsonResponse({"status":"error","msg":"Gaji Pegawai tidak ada"},status=400)
        
        if p.t_tetap is None:
            return JsonResponse({'status':"error","msg":"Tunjangan tetap tidak ada"},status=400)
        if cm == 0:
            if cm_ke < 3:
                gaji_cm = int(p.gaji) + int(p.t_tetap)
            else:
                gaji_cm = 0
        else:
            gaji_cm = 0
        # perhitungan pembagian gaji
        gaji_p = round((p.gaji / pembagi) * thk, -2)
        tt_p = round((p.t_tetap / pembagi) * thk, -2)
        tj_p = round((p.t_jabatan / pembagi) * thk, -2)
        mk_p = round((ntmk / pembagi) * thk, -2)
        ijin = [i for i in dijin if int(i["idp"]) == int(p.pk)]
        nbtk = p.tk_premi
        nbks = p.ks_premi
        bpjs = nbtk + nbks

        piutang = piutang_db.objects.using(cabang).filter(pegawai_id=p.pk,pemutihan=0).last()
        rg = gaji_db.objects.using(cabang).filter(pegawai__userid=int(p.userid)).last()

        if rg is not None:
            if rg.status_potpiutang == 1:
                pot_piutang = rg.pot_piutang
            else:
                if piutang is not None:
                    pot_piutang = piutang.pot_piutang
                else:
                    pot_piutang = 0
        else:
            if piutang is not None:
                pot_piutang = piutang.pot_piutang
            else:
                pot_piutang = 0


        ket = ""
        obj = {
            "id": p.pk,
            "status_id":p.status_id,
            "periode":bulan,
            "tahun":tahun,
            "pot": 0, # janga lupa, tanya...
            "pot_rp": 0,
            "pot_hr": 0,
            "bpjs": 0,
            "pot_piutang":0,
            "tk": p.tk_premi,
            "ks": p.ks_premi,
            "ntmk": 0,
            "gaji_cm":0,
            "insentif": 0,
            "tj": 0,
            "tt": 0,
            "ket": ket,
            "dthp": 0,
            "rek": p.rek_sd_id,
        }
    
        if len(ijin) > 0:
            print(gaji_db.objects.using(cabang).filter(pegawai__userid=int(p.userid)).exists())
            if rg is not None:
                lijin = ijin[-1]
                if lijin["sdp"] < 4:
                    sdp = 0
                else:
                    sdp = lijin["sdp"] - 3


                if rg.status_ebpjs_ks == 1:
                    nbks = rg.bpjs_ks
                else:
                    nbks = p.ks_premi

                if rg.status_ebpjs_tk == 1:
                    nbtk = rg.bpjs_tk
                else:
                    nbtk = p.tk_premi
                
                if rg.status_pothr == 1:
                    pth = rg.pot_hari
                else:
                    pth = lijin["sb"] + lijin["af"] + lijin["sdl"] + lijin["ijin"] + int(sdp)
                
                
                
                ptg = pth * potongan.potongan
                if lijin["insentif"] is None:
                    insentif = 0
                else:
                    insentif = lijin["insentif"]
                
                ket = lijin["ket"]
                
                if p.t_c == "None" or p.t_c is None:
                    pass
                elif p.t_c == 'Transer_proporsional' or p.t_c == 'Cash_proporsional':
                    # ditambah potongan piutang
                    thp = (gaji_p + tt_p + tj_p + mk_p + insentif + gaji_cm) - (bpjs + ptg + pot_piutang)
                    rg.gaji = gaji_p
                    rg.thp = thp
                    rg.pot_rupiah  = ptg
                    rg.pot_hari = pth
                    rg.t_masakerja = mk_p
                    rg.insentif = insentif
                    rg.t_jabatan = tj_p
                    rg.t_tetap = tt_p
                    rg.pot_piutang = pot_piutang
                    # rg = ket
                    rg.rek_sd_id = p.rek_sd.pk
                    rg.tgl_bayar = tgl_transfer
                    rg.bpjs = bpjs
                    rg.bpjs_ks = nbks
                    rg.bpjs_tk = nbtk
                    rg.gaji_cm = gaji_cm
                    rg.edit_by = username
                    rg.save(using=cabang)

                else:
                    if cm == 0:

                        thp = (p.gaji + p.t_tetap + p.t_jabatan + ntmk + insentif) - (bpjs + ptg + pot_piutang)
                        print(thp)
                        rg.gaji = p.gaji
                        rg.thp = thp
                        rg.pot_rupiah  = ptg
                        rg.pot_hari = pth
                        rg.pot_piutang = pot_piutang
                        rg.t_masakerja = ntmk
                        rg.insentif = insentif
                        rg.t_jabatan = p.t_jabatan
                        rg.t_tetap = p.t_tetap
                        # rg = ket
                        rg.rek_sd_id = p.rek_sd.pk
                        rg.tgl_bayar = tgl_transfer
                        rg.bpjs = bpjs
                        rg.bpjs_ks = nbks
                        rg.bpjs_tk = nbtk
                        rg.gaji_cm = 0
                        rg.edit_by = username
                        rg.save(using=cabang)
                    else:
                        thp = (gaji_cm) - (pot_piutang + bpjs)
                        rg.gaji = 0
                        rg.thp = thp
                        rg.pot_rupiah  = 0
                        rg.pot_hari = 0
                        rg.pot_piutang = pot_piutang
                        rg.t_masakerja = 0
                        rg.insentif = 0
                        rg.t_jabatan = 0
                        rg.t_tetap = 0
                        # rg = ket
                        rg.rek_sd_id = p.rek_sd.pk
                        rg.tgl_bayar = tgl_transfer
                        rg.bpjs = bpjs
                        rg.bpjs_ks = nbks
                        rg.bpjs_tk = nbtk
                        rg.gaji_cm = gaji_cm
                        rg.edit_by = username
                        rg.save(using=cabang)
            else:
                if not summary_rekap_gaji_db.objects.using(cabang).filter(tgl_bayar__month=bulan, tgl_bayar__year=tahun,status_pegawai_id=int(status)).exists():
                    lijin = ijin[-1]
                    if lijin["sdp"] < 4:
                        sdp = 0
                    else:
                        sdp = lijin["sdp"] - 3
                    
                    
                    pth = lijin["sb"] + lijin["af"] + lijin["sdl"] + lijin["ijin"] + int(sdp)
                    ptg = pth * potongan.potongan
                    if lijin["insentif"] is None:
                        insentif = 0
                    else:
                        insentif = lijin["insentif"]
                    
                    ket = lijin["ket"]

                    if p.t_c == "None" or p.t_c is None:
                        pass
                    elif p.t_c == 'Transer_proporsional' or p.t_c == 'Cash_proporsional':
                        # ditambah potongan piutang
                        thp = (gaji_p + tt_p + tj_p + mk_p + insentif + gaji_cm) - (bpjs + ptg + pot_piutang)
                        obj["pot_rp"] = ptg
                        obj["pot_hr"] = pth
                        obj["ntmk"] = mk_p
                        obj["insentif"] = insentif
                        obj["tj"] = tj_p
                        obj["pot_piutang"] = pot_piutang
                        obj["tt"] = tt_p
                        obj["ket"] = ket
                        obj["dthp"] = thp
                        obj['gaji_cm'] = gaji_cm
                        obj['gaji'] = gaji_p
                        datarg.append(obj)
                    else:
                        if cm == 0:
                            thp = (p.gaji + p.t_tetap + p.t_jabatan + ntmk + insentif) - (bpjs + ptg + pot_piutang)
                            obj["pot_rp"] = ptg
                            obj["pot_hr"] = pth
                            obj["ntmk"] = ntmk
                            obj["insentif"] = insentif
                            obj["tj"] = p.t_jabatan
                            obj["tt"] = p.t_tetap
                            obj["pot_piutang"] = pot_piutang
                            obj["dthp"] = thp
                            obj["ket"] = ket
                            obj["gaji_cm"] = 0
                            obj["gaji"] = p.gaji
                            datarg.append(obj)
                        else:
                            thp = (gaji_cm) - (bpjs + pot_piutang)
                            obj["pot_rp"] = 0
                            obj["pot_hr"] = 0
                            obj["pot_piutang"] = pot_piutang
                            obj["ntmk"] = 0
                            obj["insentif"] = 0
                            obj["tj"] = 0
                            obj["tt"] = 0
                            obj["dthp"] = thp
                            obj["ket"] = ket
                            obj["gaji_cm"] = gaji_cm
                            obj["gaji"] = 0
                            datarg.append(obj)
                else:
                    pass
                # pass
        else:
            if rg is not None:
                if rg.status_ebpjs_ks == 1:
                    nbks = rg.bpjs_ks
                else:
                    nbks = p.ks_premi

                if rg.status_ebpjs_tk == 1:
                    nbtk = rg.bpjs_tk
                else:
                    nbtk = p.tk_premi
                
                if rg.status_pothr == 1:
                    pth = rg.pot_hari
                else:
                    pth = 0
                pth = 0 
                ptg = 0
                insentif = 0


                if p.t_c == "None" or p.t_c is None:
                    pass
                elif p.t_c == "Cash_proporsional" or p.t_c == "Transfer_proporsional":
                    thp = (gaji_p + tt_p + tj_p + mk_p + insentif + gaji_cm) - (ptg + bpjs + pot_piutang)
                    rg.gaji = gaji_p
                    rg.thp = thp
                    rg.pot_rupiah  = ptg
                    rg.pot_hari = pth
                    rg.pot_piutang = pot_piutang
                    rg.t_masakerja = mk_p
                    rg.insentif = insentif
                    rg.t_jabatan = tj_p
                    rg.t_tetap = tt_p
                    # rg = ket
                    rg.rek_sd_id = p.rek_sd.pk
                    rg.tgl_bayar = tgl_transfer
                    rg.bpjs = bpjs
                    rg.bpjs_ks = nbks
                    rg.bpjs_tk = nbtk
                    rg.gaji_cm = gaji_cm
                    rg.edit_by = username
                    rg.save(using=cabang)
                else:
                    if cm == 0:
                        thp = (p.gaji + p.t_tetap + p.t_jabatan + ntmk + insentif) - (ptg + bpjs + pot_piutang)
                        rg.gaji = p.gaji
                        rg.thp = thp
                        rg.insentif = insentif
                        rg.t_tetap = p.t_tetap
                        rg.t_jabatan = p.t_jabatan
                        rg.t_masakerja = ntmk
                        rg.pot_hari = pth
                        rg.pot_rupiah = ptg
                        rg.pot_piutang = pot_piutang
                        rg.bpjs_ks = nbks
                        rg.bpjs_tk = nbtk
                        rg.bpjs = bpjs
                        rg.tgl_bayar = tgl_transfer
                        rg.rek_sd_id = p.rek_sd.pk
                        rg.gaji_cm = 0
                        rg.edit_by = username
                        rg.save(using=cabang)
                    else:
                        thp = (gaji_cm) - (bpjs + pot_piutang)
                        rg.thp = thp
                        rg.gaji = 0
                        rg.pot_rupiah  = 0
                        rg.pot_hari = 0
                        rg.pot_piutang = pot_piutang
                        rg.t_masakerja = 0
                        rg.insentif = 0
                        rg.t_jabatan = 0
                        rg.t_tetap = 0
                        # rg = ket
                        rg.rek_sd_id = p.rek_sd.pk
                        rg.tgl_bayar = tgl_transfer
                        rg.bpjs = bpjs
                        rg.bpjs_ks = p.ks_premi
                        rg.bpjs_tk = p.tk_premi
                        rg.gaji_cm = gaji_cm
                        rg.edit_by = username
                        rg.save(using=cabang)
            else:
                if not summary_rekap_gaji_db.objects.using(cabang).filter(tgl_bayar__month=bulan, tgl_bayar__year=tahun, status_pegawai_id=int(status)):
                    insentif = 0
                    ptg = 0
                    pth = 0
                    if p.t_c == "None" or p.t_c is None:
                        pass
                    elif p.t_c == "Transfer_proporsional" or p.t_c == "Cash_proporsional":
                        thp = (gaji_p + tt_p + tj_p + mk_p + insentif + gaji_cm) - (ptg + bpjs + pot_piutang)
                        obj["dthp"] = thp
                        obj["insentif"] = insentif
                        obj["pot_hr"] = pth
                        obj["pot_rp"] = ptg
                        obj["pot_piutang"] = pot_piutang
                        obj["ntmk"] = mk_p
                        obj["tj"] = tj_p
                        obj["tt"] = tt_p
                        obj["gaji_cm"] = gaji_cm
                        obj["gaji"] = gaji_p
                        datarg.append(obj)
                    else:
                        if cm == 0:
                            thp = (p.gaji + p.t_tetap + p.t_jabatan + insentif + ntmk) - (bpjs + ptg + pot_piutang)
                            obj["dthp"] = thp
                            obj["tt"] = p.t_tetap
                            obj["tj"] = p.t_jabatan
                            obj["insentif"] = insentif
                            obj["ntmk"] = ntmk
                            obj["pot_rp"] = ptg
                            obj["pot_hr"] = pth
                            obj["pot_piutang"] = pot_piutang
                            obj["gaji_cm"] = 0
                            obj["gaji"] = p.gaji
                            datarg.append(obj)
                        else:
                            thp = (gaji_cm) - (bpjs + pot_piutang)
                            obj["dthp"] = thp
                            obj["tt"] = 0
                            obj["tj"] = 0
                            obj["insentif"] = 0
                            obj["ntmk"] = 0
                            obj["pot_rp"] = 0
                            obj["pot_hr"] = 0
                            obj["pot_piutang"] = pot_piutang
                            obj["gaji_cm"] = gaji_cm
                            obj["gaji"] = 0
                            datarg.append(obj)
                else:
                    pass


    for g in datarg:
        gaji_db(
            pegawai_id=g["id"],
            status_pegawai_id=g["status_id"],
            periode=g["periode"],
            tahun=g["tahun"],
            tgl_bayar=tgl_transfer,
            t_masakerja=g["ntmk"],
            t_jabatan=g["tj"],
            t_tetap=g['tt'], 
            insentif=g["insentif"],
            pot_hari=g["pot_hr"],
            pot_rupiah=g["pot_rp"],
            pot_piutang=g["pot_piutang"],
            bpjs=g["bpjs"],
            bpjs_ks=g['ks'],
            bpjs_tk=g['tk'],
            gaji=g['gaji'],
            thp=g['dthp'],
            gaji_cm=g['gaji_cm'],
            rek_sd_id=g["rek"],
            add_by=username
        ).save(using=cabang)
    
    gaji = gaji_db.objects.select_related("pegawai","pegawai__divisi").using(cabang).filter(status_pegawai_id=int(status),status=0)
    datag = []
    for ga in gaji:
        objg = {
            'id':ga.pk,
            "pegawai":ga.pegawai.nama,
            'nik':ga.pegawai.nik,
            "bagian":ga.pegawai.divisi.divisi,
            "gaji":int(ga.pegawai.gaji),
            "gaji_t":int(ga.pegawai.gaji) + int(ga.t_masakerja) + int(ga.t_jabatan) + int(ga.t_tetap) + int(ga.insentif),
            "gaji_cm":ga.gaji_cm,
            'insentif':ga.insentif,
            'tahun':ga.tahun,
            'periode':ga.periode,
            "pot_piutang":ga.pot_piutang,
            "pot_hari":ga.pot_hari,
            "bpjs_tk":ga.bpjs_tk,
            "bpjs_ks":ga.bpjs_ks,
            "total_pot":int(ga.pot_rupiah) + int(ga.bpjs) + int(ga.pot_piutang),
            'tunjangan_masakerja':ga.t_masakerja,
            'tunjangan_jabatan':ga.t_jabatan,
            'tunjangan_tetap':ga.t_tetap,
            'pot_rupiah':ga.pot_rupiah,
            'total_bpjs':ga.bpjs,
            'total_gaji':ga.thp,        }
        datag.append(objg)

    return JsonResponse({"status":"success","msg":"Berhasil mangambil data gaji","data":datag})


@login_required
def edit_payroll(r):
    # Memastikan request hanya dari ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        id = r.POST.get("id")
        pot_hari = r.POST.get("pot_hari")
        pot_piutang = r.POST.get("pot_piutang")
        bpjs_ks = r.POST.get("bpjs_ks")
        bpjs_tk = r.POST.get("bpjs_tk")
        print(pot_hari,pot_piutang,bpjs_ks,bpjs_tk)
        with transaction.atomic(using=r.session["ccabang"]):
            try:
                    # Convert data ke integer
                    id = int(id)
                    pot_hari = int(pot_hari)
                    pot_piutang = int(pot_piutang)
                    bpjs_ks = int(bpjs_ks)
                    bpjs_tk = int(bpjs_tk)

                    # Ambil gaji terakhir
                    gaji = gaji_db.objects.using(r.session["ccabang"]).filter(id=id).last()


                    # Cek jika gaji tidak ada maka return error
                    if gaji is None:
                        return JsonResponse({"status":'error',"msg":"Data tidak ada"},status=400)

                    # Jika data didalam database berbeda dengan yang di body request maka update data didalam database lalu set status field jadi 1
                    if gaji.pot_hari != pot_hari:
                        # Update data didatabase
                        gaji.pot_hari = pot_hari
                        gaji.status_pothr = 1

                    if gaji.pot_piutang != pot_piutang:
                        gaji.pot_piutang = pot_piutang
                        gaji.status_potpiutang = 1

                    if gaji.bpjs_ks != bpjs_ks:
                        gaji.bpjs_ks = bpjs_ks
                        gaji.status_ebpjs_ks = 1

                    if gaji.bpjs_tk != bpjs_tk:
                        gaji.bpjs_tk = bpjs_tk
                        gaji.status_ebpjs_tk = 1

                    gaji.save(using=r.session["ccabang"])
                    return JsonResponse({"status":'success',"msg":"Berhasil update"},status=200)
            except Exception as e:
                print(e)
                transaction.set_rollback(True,r.session["ccabang"])
                return JsonResponse({"status":"error","msg":"Terjadi kesalahan"},status=400)
    else:
        return JsonResponse({"status":"error","msg":"Not Found"},status=400)

@login_required
def bcsv(r):
    statusid = r.POST.get("statusid")


    today = date.today()
    username = r.user.username

    bulan_ini = today.month
    tahun_ini = today.year
    hari_ini = today.day
    # Define periode
    with transaction.atomic(using=r.session["ccabang"]):
        try:
            sm = summary_rekap_gaji_db.objects.using(r.session["ccabang"]).filter(status_pegawai_id=int(statusid)).last()
            print(sm.tgl_bayar)
            if sm is None:
                return JsonResponse({"status":"error","msg":"rekap gaji tidak ada"},status=400)
            ltbayar = sm.tgl_bayar
            if ltbayar.month == 12:
                periode_gaji = 1
                tahun_gaji = int(ltbayar.year) + 1
            else:
                periode_gaji = int(ltbayar.month) + 1
                tahun_gaji = int(ltbayar.year)
            b_31 = [1, 3, 5, 7, 10, 10, 12]
            # define tahun kabisat
            if (tahun_gaji % 400 == 0) and (tahun_gaji % 100 == 0):
                kabisat = 1
            elif (tahun_gaji % 4 == 0) and (tahun_gaji % 100 != 0):
                kabisat = 1
            else:
                kabisat = 0
            # Define tgl transfer/bayar payroll (25 < tgl < 6)
            if periode_gaji == 2:
                if kabisat == 0:
                    ftgl = "{}-{}-{}".format(tahun_gaji, periode_gaji, 28)
                else:
                    ftgl = "{}-{}-{}".format(tahun_gaji, periode_gaji, 29)
            else:
                if int(periode_gaji) in b_31:
                    ftgl = "{}-{}-{}".format(tahun_gaji, int(periode_gaji), 31)
                else:
                    ftgl = "{}-{}-{}".format(tahun_gaji, int(periode_gaji), 30)
            lasttrans = ttrans_db.objects.using(r.session["ccabang"]).filter(jenis_transfer__iregex=r"Payroll").last()
            if lasttrans is not None:
                if lasttrans.tanggal_transfer.month == periode_gaji and lasttrans.tanggal_transfer.year == tahun_gaji and lasttrans.tanggal_transfer.day > 25:
                    trans = ttrans_db.objects.using(r.session["ccabang"]).get(jenis_transfer__iregex=r"Payroll")
                    tbayar = trans.tanggal_transfer
                else:
                    tgl = datetime.strptime(ftgl,"%Y-%m-%d")
                    tbayar = tgl.date()
            else:
                tgl = datetime.strptime(ftgl,"%Y-%m-%d")
                tbayar = tgl.date()
            for g in gaji_db.objects.using(r.session["ccabang"]).filter(status_pegawai_id=int(statusid),tgl_bayar=tbayar,status=0):
                g.status=1
                g.edit_by = username
                g.save(using=r.session["ccabang"])
            return JsonResponse({"status":"success","msg":"Berhasil"},status=200)    
        except Exception as e:
            print(e)
            transaction.set_rollback(True,using=r.session["ccabang"])
            return JsonResponse({"status":"error","msg":"Terjadi kesalahan"},status=400)
    return JsonResponse({"status":"success","msg":"Berhasil"},status=200)




@login_required
def csvp(r):
    if r.method == "POST":
        sid = r.POST.get("sid")
        cabang = r.session["ccabang"]
        status = status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').all()
        sm = summary_rekap_gaji_db.objects.using(cabang).filter(status_pegawai_id=int(sid)).last()
        if sm is None:
            return JsonResponse({"status":"error","msg":"rekap gaji tidak ada"},status=400)
        ltbayar = sm.tgl_bayar
        if ltbayar.month == 12:
            periode_gaji = 1
            tahun_gaji = int(ltbayar.year) + 1
        else:
            periode_gaji = int(ltbayar.month) + 1
            tahun_gaji = int(ltbayar.year)
        b_31 = [1, 3, 5, 7, 10, 10, 12]
        # define tahun kabisat
        if (tahun_gaji % 400 == 0) and (tahun_gaji % 100 == 0):
            kabisat = 1
        elif (tahun_gaji % 4 == 0) and (tahun_gaji % 100 != 0):
            kabisat = 1
        else:
            kabisat = 0
        # Define tgl transfer/bayar payroll (25 < tgl < 6)
        if periode_gaji == 2:
            if kabisat == 0:
                ftgl = "{}-{}-{}".format(tahun_gaji, periode_gaji, 28)
            else:
                ftgl = "{}-{}-{}".format(tahun_gaji, periode_gaji, 29)
        else:
            if int(periode_gaji) in b_31:
                ftgl = "{}-{}-{}".format(tahun_gaji, int(periode_gaji), 31)
            else:
                ftgl = "{}-{}-{}".format(tahun_gaji, int(periode_gaji), 30)
        lasttrans = ttrans_db.objects.using(cabang).filter(jenis_transfer__iregex=r"Payroll").last()
        if lasttrans is not None:
            if lasttrans.tanggal_transfer.month == periode_gaji and lasttrans.tanggal_transfer.year == tahun_gaji and lasttrans.tanggal_transfer.day > 25:
                trans = ttrans_db.objects.using(cabang).get(jenis_transfer__iregex=r"Payroll")
                tbayar = trans.tanggal_transfer
            else:
                tgl = datetime.strptime(ftgl,"%Y-%m-%d")
                tbayar = tgl.date()
        else:
            tgl = datetime.strptime(ftgl,"%Y-%m-%d")
            tbayar = tgl.date()
        data = []
        for rek in rekening_db.objects.using(cabang).all():
            totalGaji = gaji_db.objects.using(cabang).filter(status_pegawai__id=int(sid),rek_sd_id=int(rek.pk)).aggregate(bayar=Sum("thp"),count=Count("id"))
            obj = {
                'id_sd':rek.pk,
                "rek":rek.norek,
                "nama":rek.atas_nama,
                "alias":rek.alias,
                'mata_uang':'IDR',
                'gaji':totalGaji["bayar"],
                'keterangan':f"Gaji {nama_bulan(tbayar.month)}-{tbayar.year}",
                'total_rek':totalGaji["count"],
                'tanggal_bayar':datetime.strftime(tbayar,"%Y-%m-%d"),
                'email':rek.email,
                'data':[]
            }
            print(obj)
            for g in gaji_db.objects.using(cabang).filter(status_pegawai__id=int(sid),rek_sd_id=int(rek.pk)):
                ga = {
                    'rek':g.pegawai.no_rekening if g.pegawai.no_rekening is not None else None,
                    'nama':g.pegawai.nama,
                    'mata_uang':"IDR",
                    'gaji':g.thp if g.thp is not None or g.thp != 0 else g.gaji_cm,
                    'keterangan':f"Gaji {nama_bulan(g.tgl_bayar.month)} {g.tgl_bayar.year}",
                }
                obj["data"].append(ga)
            data.append(obj)
        return render(r,"payroll/csvp/csvp.html",{"data":data,"sid":sid,"status":status})
            

@login_required
def batalKonfirmasi(r):
    if r.method == "POST":
        status = r.POST.get("status")
        try:
            status = int(status)
            for g in gaji_db.objects.using(r.session["ccabang"]).filter(status_pegawai_id=status):
                g.status = 0
                g.save(using=r.session["ccabang"])
            return redirect("payroll",sid=status)
        except:
            messages.error(r,"Terjadi kesalahan")
            return redirect("")
        
@login_required
def konfirmasi(r):
    if r.method == "POST":
        status = r.POST.get("status")
        cabang = r.session["ccabang"]
        username = r.user.username
        print("OKOKOk")
        try:
            status = int(status)
            if not status_pegawai_db.objects.using(r.session["ccabang"]).filter(pk=status).exists():
                return JsonResponse({"status":'error',"msg":"Status pegawai tidak ada"},status=400)
            
            sm = summary_rekap_gaji_db.objects.using(cabang).filter(status_pegawai_id=int(status)).last()
            if sm is None:
                return JsonResponse({"status":"error","msg":"rekap gaji tidak ada"},status=400)
            ltbayar = sm.tgl_bayar
            if ltbayar.month == 12:
                periode_gaji = 1
                tahun_gaji = int(ltbayar.year) + 1
            else:
                periode_gaji = int(ltbayar.month) + 1
                tahun_gaji = int(ltbayar.year)
            b_31 = [1, 3, 5, 7, 10, 10, 12]
            # define tahun kabisat
            if (tahun_gaji % 400 == 0) and (tahun_gaji % 100 == 0):
                kabisat = 1
            elif (tahun_gaji % 4 == 0) and (tahun_gaji % 100 != 0):
                kabisat = 1
            else:
                kabisat = 0
            # Define tgl transfer/bayar payroll (25 < tgl < 6)
            if periode_gaji == 2:
                if kabisat == 0:
                    ftgl = "{}-{}-{}".format(tahun_gaji, periode_gaji, 28)
                else:
                    ftgl = "{}-{}-{}".format(tahun_gaji, periode_gaji, 29)
            else:
                if int(periode_gaji) in b_31:
                    ftgl = "{}-{}-{}".format(tahun_gaji, int(periode_gaji), 31)
                else:
                    ftgl = "{}-{}-{}".format(tahun_gaji, int(periode_gaji), 30)
            lasttrans = ttrans_db.objects.using(cabang).filter(jenis_transfer__iregex=r"Payroll").last()
            if lasttrans is not None:
                if lasttrans.tanggal_transfer.month == periode_gaji and lasttrans.tanggal_transfer.year == tahun_gaji and lasttrans.tanggal_transfer.day > 25:
                    trans = ttrans_db.objects.using(cabang).get(jenis_transfer__iregex=r"Payroll")
                    tbayar = trans.tanggal_transfer
                else:
                    tgl = datetime.strptime(ftgl,"%Y-%m-%d")
                    tbayar = tgl.date()
            else:
                tgl = datetime.strptime(ftgl,"%Y-%m-%d")
                tbayar = tgl.date()
            
            jtransaksi = jenis_transaksi_db.objects.using(r.session["ccabang"]).filter(jenis_transaksi__iregex=r"Pembayaran by payroll").last()

            if jtransaksi is None:
                messages.error(r,"Jenis transaksi tidak ada")
                return redirect("payroll",sid=status)

            for g in gaji_db.objects.using(r.session["ccabang"]).raw("select gaji.id, gaji.pot_piutang as gpot_piutang, piutang.pegawai_id as idp from payroll_app_gaji_db as gaji join payroll_app_piutang_db as piutang on gaji.pegawai_id=piutang.pegawai_id"):
                piutang = piutang_db.objects.using(r.session["ccabang"]).filter(pegawai_id=g.idp).last()
                if piutang.piutang != 0 and g.gpot_piutang != 0:
                    totalPiutang = piutang.piutang - g.gpot_piutang
                    print(totalPiutang,g.gpot_piutang)
                    piutang.piutang = totalPiutang
                    piutang.save() 

                    transaksi_db.objects.using(r.session["ccabang"]).create(
                        tgl=tbayar,
                        pegawai_id=g.idp,
                        nilai=g.gpot_piutang,
                        jenis_transaksi_id=jtransaksi.pk
                    )
                    setRedisTransaksi(r.session["ccabang"],g.idp)
            # if summary_rekap_gaji_db.objects.using(r.session["ccabang"])  
            rekap = gaji_db.objects.using(r.session["ccabang"]).filter(periode=tbayar.month, tahun=tbayar.year,status_pegawai_id=status).aggregate(piutang=Sum("pot_piutang"),ttetap=Sum("t_tetap"),tjabatan=Sum("t_jabatan"),tmasakerja=Sum("t_masakerja"),insentif=Sum("insentif"),absensi=Sum("pot_rupiah"),bpjs_tk=Sum("bpjs_tk"),bpjs_ks=Sum("bpjs_ks"),gaji_cm=Sum("gaji_cm"),gaji=Sum("gaji"),thp=Sum("thp"))
            print(tbayar.month,status)
            summary_rekap_gaji_db(
                status_pegawai_id=status,
                tgl_bayar=tbayar,
                total_gaji_bruto=rekap["gaji"],
                total_tmasakerja=rekap["tmasakerja"],
                total_ttetap=rekap["ttetap"],
                total_tjabatan=rekap["tjabatan"],
                total_insentif=rekap["insentif"],
                total_pot_piutang=rekap["piutang"],
                total_pot_absensi=rekap["absensi"],
                total_bpjs_tk=rekap["bpjs_tk"],
                total_bpjs_ks=rekap["bpjs_ks"],
                total_gaji_cm=rekap["gaji_cm"],
                total_bayar_gaji=rekap["thp"],
                add_by=username
            ).save(using=r.session["ccabang"])


            gaji_db.objects.using(r.session["ccabang"]).filter(periode=tbayar.month, tahun=tbayar.year,status_pegawai_id=status).delete()
            return redirect("payroll",sid=status)
        except Exception as e:
            print(e)
            messages.error(r,"Terjadi kesalahan")
            return redirect("payroll",sid=status)



@login_required
def printC(r):
    if r.method == "POST":
        sd = r.POST.get("sd")
        sid = r.POST.get("sid")
        cabang = r.session["ccabang"]
        status = status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').all()


        try:
            sm = summary_rekap_gaji_db.objects.using(cabang).filter(status_pegawai_id=int(sid)).last()
            if sm is None:
                messages.error(r,"Rekap gaji tidak ada")
                return redirect("payroll",sid=sid)

            ltbayar = sm.tgl_bayar
            if ltbayar.month == 12:
                periode_gaji = 1
                tahun_gaji = int(ltbayar.year) + 1
            else:
                periode_gaji = int(ltbayar.month) + 1
                tahun_gaji = int(ltbayar.year)
            b_31 = [1, 3, 5, 7, 10, 10, 12]
            # define tahun kabisat
            if (tahun_gaji % 400 == 0) and (tahun_gaji % 100 == 0):
                kabisat = 1
            elif (tahun_gaji % 4 == 0) and (tahun_gaji % 100 != 0):
                kabisat = 1
            else:
                kabisat = 0
            # Define tgl transfer/bayar payroll (25 < tgl < 6)
            if periode_gaji == 2:
                if kabisat == 0:
                    ftgl = "{}-{}-{}".format(tahun_gaji, periode_gaji, 28)
                else:
                    ftgl = "{}-{}-{}".format(tahun_gaji, periode_gaji, 29)
            else:
                if int(periode_gaji) in b_31:
                    ftgl = "{}-{}-{}".format(tahun_gaji, int(periode_gaji), 31)
                else:
                    ftgl = "{}-{}-{}".format(tahun_gaji, int(periode_gaji), 30)
            lasttrans = ttrans_db.objects.using(cabang).filter(jenis_transfer__iregex=r"Payroll").last()
            if lasttrans is not None:
                if lasttrans.tanggal_transfer.month == periode_gaji and lasttrans.tanggal_transfer.year == tahun_gaji and lasttrans.tanggal_transfer.day > 25:
                    trans = ttrans_db.objects.using(cabang).get(jenis_transfer__iregex=r"Payroll")
                    tbayar = trans.tanggal_transfer
                else:
                    tgl = datetime.strptime(ftgl,"%Y-%m-%d")
                    tbayar = tgl.date()
            else:
                tgl = datetime.strptime(ftgl,"%Y-%m-%d")
                tbayar = tgl.date()



            data = []
            rek = rekening_db.objects.using(r.session["ccabang"]).filter(id=sd).last()
            if not rek:
                messages.error(r,"Rekening tidak ada")
                return redirect("payroll",sid=sid)
            
            if not status_pegawai_db.objects.using(r.session["ccabang"]).filter(id=sid).last():
                messages.error(r,"Status pegawai tidak ada")
                return redirect("payroll",sid=sid)

            totalGaji = gaji_db.objects.using(cabang).filter(status_pegawai__id=int(sid),rek_sd_id=int(rek.pk)).aggregate(bayar=Sum("thp"),count=Count("id"))
            obj = {
                "rek":[rek.norek],
                "nama":[rek.atas_nama],
                'mata_uang':['IDR'],
                'gaji':[totalGaji["bayar"]],
                'keterangan':[f"Gaji {nama_bulan(tbayar.month)}-{tbayar.year}"],
                'total_rek':[totalGaji["count"]],
                'tanggal_bayar':[datetime.strftime(tbayar,"%Y-%m-%d")],
                'email':[rek.email],
            }
            for g in gaji_db.objects.using(cabang).filter(status_pegawai__id=int(sid),rek_sd_id=int(rek.pk)):
                obj['rek'].append(g.pegawai.no_rekening if g.pegawai.no_rekening is not None else None)
                obj['nama'].append(g.pegawai.nama)
                obj['mata_uang'].append("IDR")
                obj['gaji'].append(g.thp if g.thp is not None or g.thp != 0 else g.gaji_cm)
                obj['keterangan'].append(f"Gaji {nama_bulan(g.tgl_bayar.month)} {g.tgl_bayar.year}")
                obj['total_rek'].append("")
                obj['tanggal_bayar'].append("")
                obj['email'].append("")
            df = pd.DataFrame(obj)
            df.to_csv(f'static/excel/payroll {rek.nama_rekening} {tbayar.month} {tbayar.year}.csv',header=False,index=False)
            with open(f'static/excel/payroll {rek.nama_rekening} {tbayar.month} {tbayar.year}.csv',"rb") as f:
                for l in os.listdir("static/excel/"):
                    os.remove(f"static/excel/{l}")
                file = HttpResponse(f.read(),content_type="application/vnd.ms-excel")
                file["Content-Disposition"] = f'attachment; filename=payroll {rek.nama_rekening} {tbayar.month} {tbayar.year}.csv'
                return file
        except Exception as e:
            messages.error(r,e)
            return redirect("payroll",sid=sid)
        
@login_required
def printP(r):
    if r.method == "POST":
        sd = r.POST.get("sd")
        sid = r.POST.get("sid")
        cabang = r.session["ccabang"]
        status = status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').all()


        try:
            sm = summary_rekap_gaji_db.objects.using(cabang).filter(status_pegawai_id=int(sid)).last()
            if sm is None:
                messages.error(r,"Rekap gaji tidak ada")
                return redirect("payroll",sid=sid)

            ltbayar = sm.tgl_bayar
            if ltbayar.month == 12:
                periode_gaji = 1
                tahun_gaji = int(ltbayar.year) + 1
            else:
                periode_gaji = int(ltbayar.month) + 1
                tahun_gaji = int(ltbayar.year)
            b_31 = [1, 3, 5, 7, 10, 10, 12]
            # define tahun kabisat
            if (tahun_gaji % 400 == 0) and (tahun_gaji % 100 == 0):
                kabisat = 1
            elif (tahun_gaji % 4 == 0) and (tahun_gaji % 100 != 0):
                kabisat = 1
            else:
                kabisat = 0
            # Define tgl transfer/bayar payroll (25 < tgl < 6)
            if periode_gaji == 2:
                if kabisat == 0:
                    ftgl = "{}-{}-{}".format(tahun_gaji, periode_gaji, 28)
                else:
                    ftgl = "{}-{}-{}".format(tahun_gaji, periode_gaji, 29)
            else:
                if int(periode_gaji) in b_31:
                    ftgl = "{}-{}-{}".format(tahun_gaji, int(periode_gaji), 31)
                else:
                    ftgl = "{}-{}-{}".format(tahun_gaji, int(periode_gaji), 30)
            lasttrans = ttrans_db.objects.using(cabang).filter(jenis_transfer__iregex=r"Payroll").last()
            if lasttrans is not None:
                if lasttrans.tanggal_transfer.month == periode_gaji and lasttrans.tanggal_transfer.year == tahun_gaji and lasttrans.tanggal_transfer.day > 25:
                    trans = ttrans_db.objects.using(cabang).get(jenis_transfer__iregex=r"Payroll")
                    tbayar = trans.tanggal_transfer
                else:
                    tgl = datetime.strptime(ftgl,"%Y-%m-%d")
                    tbayar = tgl.date()
            else:
                tgl = datetime.strptime(ftgl,"%Y-%m-%d")
                tbayar = tgl.date()



            data = []
            rek = rekening_db.objects.using(r.session["ccabang"]).filter(id=sd).last()
            if not rek:
                messages.error(r,"Rekening tidak ada")
                return redirect("payroll",sid=sid)
            
            if not status_pegawai_db.objects.using(r.session["ccabang"]).filter(id=sid).last():
                messages.error(r,"Status pegawai tidak ada")
                return redirect("payroll",sid=sid)

            totalGaji = gaji_db.objects.using(cabang).filter(status_pegawai__id=int(sid),rek_sd_id=int(rek.pk)).aggregate(bayar=Sum("thp"),count=Count("id"))
            data = {
                "rek":rek.norek,
                "nama":rek.atas_nama,
                'mata_uang':'IDR',
                'gaji':totalGaji["bayar"],
                'keterangan':f"Gaji {nama_bulan(tbayar.month)}-{tbayar.year}",
                'total_rek':totalGaji["count"],
                'tanggal_bayar':datetime.strftime(tbayar,"%Y-%m-%d"),
                'email':rek.email,
                "data":[]
            }
            for g in gaji_db.objects.using(cabang).filter(status_pegawai__id=int(sid),rek_sd_id=int(rek.pk)):
                obj = {
                 'rek':g.pegawai.no_rekening if g.pegawai.no_rekening is not None else None,
                 'nama':g.pegawai.nama,
                 'mata_uang':"IDR",
                 'gaji':g.thp if g.thp is not None or g.thp != 0 else g.gaji_cm,
                 'keterangan':f"Gaji {nama_bulan(g.tgl_bayar.month)} {g.tgl_bayar.year}",
                }
                data["data"].append(obj)
            return render(r,"payroll/laporan/pdf.html",{"data":data})
        except Exception as e:
            messages.error(r,e)
            return redirect("payroll",sid=sid)
