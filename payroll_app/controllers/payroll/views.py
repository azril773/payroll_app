from ..lib import *
# Create your views here.
@authorization(["root","it"])
def payroll(r,sid):
    iduser = r.session["user"]["id"]
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
        "staff":r.session["user"]["admin"],
        "sid":sid,
        'modal':modal,
        "gaji":gaji,
        "periode":nama_bulan(bulan)
    }
    return render(r,"payroll/payroll.html",data)

@authorization(["root","it"])
def payroll_json(r):
    with transaction.atomic(using=r.session['ccabang']):
        try:
            status = r.POST.get("status")

            cabang = r.session["ccabang"]
            username = r.session["user"]["nama"]
            today = date.today()
            hari_ini = today.day
            bulan_ini = today.month
            tahun_ini = today.year
            if not status_pegawai_payroll_db.objects.using(f'p{cabang}').filter(status_pegawai_id=int(status)).exists():
                print("OK")
                raise Exception("Status tidak terdaftar")
            sm = summary_rekap_gaji_db.objects.using(r.session["ccabang"]).filter(status_pegawai_id=int(status)).last()
            if  sm is None:
                raise Exception("Gaji terakhir tidak ada")
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
                raise Exception("Potongan absensi tidak ada")
            for k in data_ijin_db.objects.using(r.session["ccabang"]).filter(tahun=tahun,periode=bulan):
                data_k = {
                    "idp":k.pegawai_id,
                    "sb":k.sb,
                    "sdl":k.sdl,
                    "sdp":k.sdp,
                    "ijin":k.ijin,
                    "af":k.af,
                    "ket":k.ket
                }
                dijin.append(data_k)
                
            datarg = []
            for p in pegawai_db.objects.using(r.session["ccabang"]).filter(status_id=int(status),status_payroll=1,payroll_by__iregex=r'hrd'):
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
                    raise Exception("Gaji Pegawai tidak ada")
                
                if cm > 0:
                    if cm_ke < 3:
                        gaji_cm = int(p.gaji)
                    else:
                        gaji_cm = 0
                else:
                    gaji_cm = 0
                # perhitungan pembagian gaji
                gaji_p = round((p.gaji / pembagi) * thk, -2)
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
                    "gaji_cm":0,
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
                        ket = lijin["ket"]
                        
                        if p.t_c == "None" or p.t_c is None:
                            pass
                        elif p.t_c == 'Transer_proporsional' or p.t_c == 'Cash_proporsional':
                            # ditambah potongan piutang
                            thp = (gaji_p + gaji_cm) - (bpjs + ptg + pot_piutang)
                            rg.gaji = gaji_p
                            rg.thp = thp
                            rg.pot_rupiah  = ptg
                            rg.pot_hari = pth
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

                                thp = (p.gaji) - (bpjs + ptg + pot_piutang)
                                print(thp)
                                rg.gaji = p.gaji
                                rg.thp = thp
                                rg.pot_rupiah  = ptg
                                rg.pot_hari = pth
                                rg.pot_piutang = pot_piutang
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
                            
                            ket = lijin["ket"]

                            if p.t_c == "None" or p.t_c is None:
                                pass
                            elif p.t_c == 'Transer_proporsional' or p.t_c == 'Cash_proporsional':
                                # ditambah potongan piutang
                                thp = (gaji_p  + gaji_cm) - (bpjs + ptg + pot_piutang)
                                obj["pot_rp"] = ptg
                                obj["pot_hr"] = pth
                                obj["pot_piutang"] = pot_piutang
                                obj["ket"] = ket
                                obj["dthp"] = thp
                                obj['gaji_cm'] = gaji_cm
                                obj['gaji'] = gaji_p
                                datarg.append(obj)
                            else:
                                if cm == 0:
                                    thp = (p.gaji) - (bpjs + ptg + pot_piutang)
                                    obj["pot_rp"] = ptg
                                    obj["pot_hr"] = pth
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


                        if p.t_c == "None" or p.t_c is None:
                            pass
                        elif p.t_c == "Cash_proporsional" or p.t_c == "Transfer_proporsional":
                            thp = (gaji_p + gaji_cm) - (ptg + bpjs + pot_piutang)
                            rg.gaji = gaji_p
                            rg.thp = thp
                            rg.pot_rupiah  = ptg
                            rg.pot_hari = pth
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
                                thp = (p.gaji ) - (ptg + bpjs + pot_piutang)
                                rg.gaji = p.gaji
                                rg.thp = thp
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
                            ptg = 0
                            pth = 0
                            if p.t_c == "None" or p.t_c is None:
                                pass
                            elif p.t_c == "Transfer_proporsional" or p.t_c == "Cash_proporsional":
                                thp = (gaji_p + gaji_cm) - (ptg + bpjs + pot_piutang)
                                obj["dthp"] = thp
                                obj["pot_hr"] = pth
                                obj["pot_rp"] = ptg
                                obj["pot_piutang"] = pot_piutang
                                obj["gaji_cm"] = gaji_cm
                                obj["gaji"] = gaji_p
                                datarg.append(obj)
                            else:
                                if cm == 0:
                                    thp = (p.gaji) - (bpjs + ptg + pot_piutang)
                                    obj["dthp"] = thp
                                    obj["pot_rp"] = ptg
                                    obj["pot_hr"] = pth
                                    obj["pot_piutang"] = pot_piutang
                                    obj["gaji_cm"] = 0
                                    obj["gaji"] = p.gaji
                                    datarg.append(obj)
                                else:
                                    thp = (gaji_cm) - (bpjs + pot_piutang)
                                    obj["dthp"] = thp
                                    obj["pot_rp"] = 0
                                    obj["pot_hr"] = 0
                                    obj["pot_piutang"] = pot_piutang
                                    obj["gaji_cm"] = gaji_cm
                                    obj["gaji"] = 0
                                    datarg.append(obj)
                        else:
                            pass

            for g in datarg:
                print(g)
                gaji_db(
                    pegawai_id=g["id"],
                    status_pegawai_id=g["status_id"],
                    periode=g["periode"],
                    tahun=g["tahun"],
                    tgl_bayar=tgl_transfer.date(),
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
                    "gaji_t":int(ga.pegawai.gaji),
                    "gaji_cm":ga.gaji_cm,
                    'tahun':ga.tahun,
                    'periode':ga.periode,
                    "pot_piutang":ga.pot_piutang,
                    "pot_hari":ga.pot_hari,
                    "bpjs_tk":ga.bpjs_tk,
                    "bpjs_ks":ga.bpjs_ks,
                    "total_pot":int(ga.pot_rupiah) + int(ga.bpjs) + int(ga.pot_piutang),
                    'pot_rupiah':ga.pot_rupiah,
                    'total_bpjs':ga.bpjs,
                    'total_gaji':ga.thp,        }
                datag.append(objg)
            print(datag)

            return JsonResponse({"status":"success","msg":"Berhasil mangambil data gaji","data":datag})
        except Exception as e:
            transaction.set_rollback(True,using=r.session["ccabang"])
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            msg = e.args[0] if e.args is not None else "Terjadi kesalahan"
            return JsonResponse({"status":"error",'msg':msg},status=400)


@authorization(["root","it"])
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
                    piutang = piutang_db.objects.using(r.session["ccabang"]).filter(pegawai_id=gaji.pegawai_id).last()
                    # Cek jika gaji tidak ada maka return error
                    if gaji is None:
                        raise Exception("Data tidak ada")
                    # Jika data didalam database berbeda dengan yang di body request maka update data didalam database lalu set status field jadi 1
                    if gaji.pot_hari != pot_hari:
                        # Update data didatabase
                        gaji.pot_hari = pot_hari
                        gaji.status_pothr = 1
                    if piutang is not None:
                        if piutang.piutang <= 0:
                            gaji.pot_piutang = 0
                        else:
                            if gaji.pot_piutang != pot_piutang:
                                if pot_piutang > piutang.piutang:
                                    raise Exception("Pot piutang lebih besar dari piutang")
                                else:
                                    gaji.pot_piutang = pot_piutang
                                    gaji.status_potpiutang = 1
                            else:
                                pass
                    else:
                        gaji.pot_piutang = 0
                    if gaji.bpjs_ks != bpjs_ks:
                        gaji.bpjs_ks = bpjs_ks
                        gaji.status_ebpjs_ks = 1
                    if gaji.bpjs_tk != bpjs_tk:
                        gaji.bpjs_tk = bpjs_tk
                        gaji.status_ebpjs_tk = 1
                    gaji.save(using=r.session["ccabang"])
                    return JsonResponse({"status":'success',"msg":"Berhasil update"},status=200)
            except Exception as e:
                transaction.set_rollback(True,r.session["ccabang"])
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                msg = e.args[0] if e.args is not None else "Terjadi kesalahan"
                return JsonResponse({"status":"error","msg":msg},status=400)
    else:
        return JsonResponse({"status":"error","msg":"Not Found"},status=400)

@authorization(["root","it"])
def bcsv(r):
    statusid = r.POST.get("statusid")


    today = date.today()
    username = r.session["user"]["nama"]

    bulan_ini = today.month
    tahun_ini = today.year
    hari_ini = today.day
    # Define periode
    with transaction.atomic(using=r.session["ccabang"]):
        try:
            sm = summary_rekap_gaji_db.objects.using(r.session["ccabang"]).filter(status_pegawai_id=int(statusid)).last()
            print(sm.tgl_bayar)
            if sm is None:
                raise Exception("rekap gaji tidak ada")
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
            transaction.set_rollback(True,using=r.session["ccabang"])
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            msg = e.args[0] if e.args is not None else "Terjadi kesalahan"
            return JsonResponse({"status":"error","msg":msg},status=400)
    return JsonResponse({"status":"success","msg":"Berhasil"},status=200)




@authorization(["root","it"])
def csvp(r):
    if r.method == "POST":
        sid = r.POST.get("sid")
        cabang = r.session["ccabang"]
        try:
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
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            messages.error(r,"Terjadi kesalahan")
            return redirect("payroll",sid=sid)

@authorization(["root","it"])
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
        
@authorization(["root","it"])
def konfirmasi(r):
    if r.method == "POST":
        status = r.POST.get("status")
        cabang = r.session["ccabang"]
        username = r.session["user"]["nama"]
        with transaction.atomic(using=r.session["ccabang"]):
            try:
                status = int(status)
                if not status_pegawai_db.objects.using(r.session["ccabang"]).filter(pk=status).exists():
                    raise Exception("Status pegawai tidak ada")
                
                sm = summary_rekap_gaji_db.objects.using(cabang).filter(status_pegawai_id=int(status)).last()
                if sm is None:
                    raise Exception("rekap gaji tidak ada")
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
                    raise Exception("Jenis transaksi tidak ada")
                

                for g in gaji_db.objects.using(r.session["ccabang"]).filter(status_pegawai_id=status):
                    piutang = piutang_db.objects.using(r.session["ccabang"]).filter(pegawai_id=g.pegawai_id).last()
                    if piutang.piutang != 0 and g.pot_piutang != 0:
                        totalPiutang = piutang.piutang - g.pot_piutang
                        if totalPiutang < piutang.pot_piutang:
                            piutang.pot_piutang = totalPiutang
                            piutang.save()
                        piutang.piutang = totalPiutang
                        piutang.save() 
                        transaksi_db.objects.using(r.session["ccabang"]).create(
                            tgl=tbayar,
                            pegawai_id=g.pegawai_id,
                            nilai=g.pot_piutang,
                            jenis_transaksi_id=jtransaksi.pk
                        )
                        setRedisTransaksi(r.session["ccabang"],g.pegawai_id)
                    if g.gaji_cm > 0:
                        history = histori_rekap_gaji_db.objects.using(r.session["ccabang"]).filter(pegawai_id=g.pegawai_id).last()
                        if not history:
                            raise Exception("History rekap gaji tidak ada")
                        cm_ke = history.cm_ke + 1
                        histori_rekap_gaji_db(
                            pegawai=g.pegawai_id,
                            nik=g.pegawai.nik,
                            divisi=g.pegawai.divisi,
                            tgl_bayar=g.tgl_bayar,
                            gaji=g.gaji,
                            cm_ke=cm_ke,
                            pot_hari=g.pot_hari,
                            pot_rupiah=g.pot_rupiah,
                            pot_piutang=g.pot_piutang,
                            bpjs_tk=g.bpjs_tk,
                            bpjs_ks=g.bpjs_ks,
                            bpjs=g.bpjs,
                            thp=g.thp,
                            rek_sumber_id=g.rek_sd_id,
                            status=g.status,
                            add_by="prog",
                        ).save(using=r.session["ccabang"])
                    else:
                        histori_rekap_gaji_db(
                            pegawai=g.pegawai_id,
                            nik=g.pegawai.nik,
                            divisi=g.pegawai.divisi,
                            tgl_bayar=g.tgl_bayar,
                            gaji=g.gaji,
                            cm_ke=0,
                            pot_hari=g.pot_hari,
                            pot_rupiah=g.pot_rupiah,
                            pot_piutang=g.pot_piutang,
                            bpjs_tk=g.bpjs_tk,
                            bpjs_ks=g.bpjs_ks,
                            bpjs=g.bpjs,
                            thp=g.thp,
                            rek_sumber_id=g.rek_sd_id,
                            status=g.status,
                            add_by="prog",
                        ).save(using=r.session["ccabang"])


                        
                # if summary_rekap_gaji_db.objects.using(r.session["ccabang"])  
                rekap = gaji_db.objects.using(r.session["ccabang"]).filter(status_pegawai_id=status).aggregate(piutang=Sum("pot_piutang"),ttetap=Sum("t_tetap"),tjabatan=Sum("t_jabatan"),absensi=Sum("pot_rupiah"),bpjs_tk=Sum("bpjs_tk"),bpjs_ks=Sum("bpjs_ks"),gaji_cm=Sum("gaji_cm"),gaji=Sum("gaji"),thp=Sum("thp"))
                summary_rekap_gaji_db(
                    status_pegawai_id=status,
                    tgl_bayar=tbayar,
                    total_gaji_bruto=rekap["gaji"],
                    total_pot_piutang=rekap["piutang"],
                    total_pot_absensi=rekap["absensi"],
                    total_bpjs_tk=rekap["bpjs_tk"],
                    total_bpjs_ks=rekap["bpjs_ks"],
                    total_gaji_cm=rekap["gaji_cm"],
                    total_bayar_gaji=rekap["thp"],
                    add_by=username
                ).save(using=r.session["ccabang"])
                gaji_db.objects.using(r.session["ccabang"]).filter(status_pegawai_id=status).delete()

                data_ijin_db.objects.using(r.session["ccabang"]).filter(pegawai__status_id=status).delete()

                
                return redirect("payroll",sid=status)
            except Exception as e:
                transaction.set_rollback(True,using=r.session["ccabang"])
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                msg = e.args[0] if e.args is not None else "Terjadi kesalahan"
                messages.error(r,msg)
                return redirect("payroll",sid=status)



@authorization(["root","it"])
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
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            messages.error(r,e)
            return redirect("payroll",sid=sid)
        
@authorization(["root","it"])
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
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            messages.error(r,e)
            return redirect("payroll",sid=sid)
