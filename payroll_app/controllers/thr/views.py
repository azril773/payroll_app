from ..lib import *



@authorization(["root","it"])
def thr(r):
    try:
        today = date.today()
        hari_ini = today.day
        bulan_ini = today.month
        tahun_ini = today.year
        cabang = r.session["ccabang"]
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

        
        tthr = ttrans_db.objects.using(r.session['ccabang']).filter(jenis_transfer__iregex=r'thr').last()
        if not tthr:
            messages.error(r,"Tanggal transfer THR tidak ada")
            return redirect("beranda")

        if tthr < today:
            messages.error(r,"Tanggal transfer belum ditentukan")
            return redirect("beranda")
        
        histori = histori_thr_db.objects.using(r.session['ccabang']).filter(tgl_bayar__year=tthr.tanggal_transfer.year).last()
        if histori is not None:
            status = 1
        else:
            data_thr = []
            for p in pegawai_db.objects.using(r.session["ccabang"]).filter(status_payroll=1):
                tgl_masuk = p.tgl_masuk
                tahun_masuk = tgl_masuk.year
                bulan_masuk = tgl_masuk.month
                tmasuk = tgl_masuk.day
                thr =  tthr.tanggal_transfer
                

                if int(tahun_masuk) != int(thr.year):
                    if int(tahun_masuk) < int(thr.year):
                        if int(bulan_masuk) == int(thr.month):
                            if int(tmasuk) < 16:
                                masa_k =  (thr.year - tahun_masuk)
                                bulan_k = None
                            else:
                                masa_k = (thr.year - tahun_masuk) - 1
                                bulan_k = None
                        else:
                            if int(bulan_masuk) < int(thr.month):
                                masa_k = (thr.year - tahun_masuk)
                                bulan_k = None
                            else:
                                masa_k = (thr.year - tahun_masuk) - 1
                                bulan_k = None

                        if masa_k <= 0 :
                            if int(tmasuk) < 16:
                                bulan = (12 - bulan_masuk) + (thr.month)
                                if bulan >= 3:
                                    bulan_k = bulan
                                else:
                                    bulan_k = 0
                            else:
                                bulan = ((12 - bulan_masuk) + (thr.month)) - 1
                                if bulan >= 3:
                                    bulan_k = bulan
                                else:
                                    bulan_k = 0
                    else:
                        masa_k = 0
                        bulan_k = 0
                else:
                    if int(bulan_masuk) < int(thr.month):
                        if int(tmasuk) < 16:
                            ctb = (thr.month - bulan_masuk)
                        else:
                            ctb = (thr.month - bulan_masuk) - 1

                        if ctb < 3:
                            masa_k = 0 
                            bulan_k = 0
                        else:
                            masa_k = 0
                            bulan_k= ctb
                    else:
                        masa_k = 0
                        bulan_k = 0
                            

                ntmk = 0
                if masa_k > 0:
                    ntmk = fmkerja_k(masa_k)
                else:
                    ntmk = 0

                if masa_k > 0:
                    gaji = p.gaji
                    tj = p.t_jabatan
                    tt = p.t_tetap
                    ntmk = ntmk
                    thr = gaji + tj + tt + ntmk
                    mkerja = "{} Thn".format(masa_k)
                elif bulan_k >= 3:
                    gaji = round((bulan_k / 12) * p.gaji, -2)
                    tj = round((bulan_k / 12) * p.t_jabatan, -2)
                    tt = round((bulan_k / 12) * p.t_tetap, -2)
                    ntmk = round((bulan_k / 12) * ntmk, -2)
                    thr = gaji + tj + tt + ntmk
                    mkerja = "{} Bln".format(bulan_k)
                else:
                    thr = 0
                    mkerja = 0

                # rek sumber dana
                if p.rek_sd_id is not None:
                    sumber = p.rek_sd.norek
                else:
                    sumber = None
                # cash / transfer
                if p.no_rekening == "0" or p.no_rekening == "":
                    ct = "Cash"
                else:
                    ct = "Transfer"


                dthr = {
                    "nama": p.nama,
                    "nik": p.nik,
                    "pnorek": p.no_rek,
                    "bagian": p.divisi,
                    "norek": sumber,
                    "mkerja": mkerja,
                    "gaji": gaji,
                    "tjabatan": tj,
                    "ttetap": tt,
                    "ntmk": ntmk,
                    "thr": thr,
                    "ct": ct,
                }
                data_thr.append(dthr)



    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return JsonResponse({"status":"error",'msg':"Terjadi kesalahan"},status=400)