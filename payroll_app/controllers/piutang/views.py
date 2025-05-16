from ..lib import *


# def setRedisTemp(cabang):
#     data = []
#     temporary = temporary_piutang_db.objects.select_related("pegawai","jenis_piutang","jenis_piutang__jenis_transaksi").using(cabang).all()
#     # Jika belum ambil semua data dari table temporary
#     for temp in temporary:
#         obj = {
#             "id":temp.pk,
#             "tanggal":str(temp.tgl),
#             "pegawai":temp.pegawai.nama,
#             "pegawai_id":temp.pegawai_id,
#             "piutang":temp.piutang,
#             "pot_piutang":temp.pot_piutang,
#             "jenis_piutang":temp.jenis_piutang.jenis_transaksi.jenis_transaksi,
#             "jenis_id":temp.jenis_piutang_id,
#         }
#         data.append(obj)
#     # Set redis untuk data dari temporary
#     redisConn.hset("post_piutang",mapping={
#         "data":json.dumps(data)
#     })
#     # Set expire data selama 5 menit
#     redisConn.expire("post_piutang",300)

# def setRedisTransaksi(cabang,idp):
#     data = []
#     transaksi = transaksi_db.objects.select_related("pegawai","jenis_transaksi","kode_piutang").using(cabang).filter(pegawai_id=int(idp))
#     # Jika belum ambil semua data dari table transaksi
#     for trans in transaksi:
#         obj = {
#             "id":trans.pk,
#             "tgl":str(trans.tgl),
#             "pegawai":trans.pegawai.nama,
#             "pegawai_id":trans.pegawai_id,
#             "nilai":trans.nilai,
#             "jenis_transaksi":trans.jenis_transaksi.jenis_transaksi,
#             "jenis_id":trans.jenis_transaksi_id,
#             "nodok":trans.nodok,
#             "kode_piutang":""
#         }
#         data.append(obj)
#     # Set redis untuk data dari transaksi
#     redisConn.hset(f"transaksi-{idp}",mapping={
#         "data":json.dumps(data)
#     })
#     # Set expire data selama 5 menit
#     redisConn.expire(f"transaksi-{idp}",300)


@authorization(["root","it"])
def piutang(r):
    pegawai = pegawai_db.objects.using(r.session["ccabang"]).filter(status_payroll=1)
    jenis = jenis_piutang_db.objects.select_related("jenis_transaksi").using(r.session["ccabang"]).all()
    jtransaksi = jenis_transaksi_db.objects.using(r.session["ccabang"]).filter(jenis_transaksi__iregex=r'pembayaran|pemutihan')
    count = temporary_piutang_db.objects.using(r.session["ccabang"]).all().aggregate(count=Count("id"))
    status_payroll = status_pegawai_payroll_db.objects.using(f"p{r.session['ccabang']}").all()
    data = {
        'pegawai':pegawai,
        'jenis':jenis,
        'countTemp':count["count"],
        'jenis_transaksi':jtransaksi,
        'status':status_payroll,
        "staff":r.session["user"]["admin"],
    }
    return render(r,"piutang/piutang.html",data)


@authorization(["root","it"])
def piutang_json(r):
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        piutang = piutang_db.objects.select_related("pegawai").using(r.session["ccabang"]).all()
        idp = [p.pegawai.pk for p in piutang]
        ketemu = ketemu_db.objects.select_related("pegawai").using(r.session["ccabang"]).filter(pegawai_id__in=idp)
        print(ketemu)
        result = []
        for pg in piutang:
            ktm = [k for k in ketemu if k.pegawai.pk == pg.pegawai.pk]
            if len(ktm) > 0:
                k = ktm[0].ketemu
            else:
                k = 0
            obj = {
                'id':pg.pk,
                "idp":pg.pegawai.pk,
                "nama":pg.pegawai.nama,
                'nik':pg.pegawai.nik,
                "piutang":pg.piutang,
                'pot':pg.pot_piutang,
                'ketemu':k
            }
            result.append(obj)
        return JsonResponse({'status':"success","msg":"Berhasil ambil data piutang","data":result},status=200)
    else:
        return JsonResponse({"status":"error","msg":"Not Found"},status=404)
@authorization(["root","it"])
def tpiutang_json(r):
    if r.headers["X-Requested-With"] == 'XMLHttpRequest':
        
        # Data form
        tanggal = r.POST.get("tanggal")
        pegawai = r.POST.get("pegawai")
        jenis = r.POST.get("jenis")
        nilai = r.POST.get("nilai")
        potongan = r.POST.get("potongan")
        username = r.session["user"]["nama"]


        # Jika form kosong
        if pegawai is None or jenis is None or nilai is None or potongan is None or tanggal is None:
            return JsonResponse({"status":"error","msg":"Form tidak boleh kosong"},status=400)
        
        # Convert tanggal menjadi format YYYY-MM-DD
        try:
            tanggal = datetime.strptime(tanggal,"%Y-%m-%d")
        except Exception as e:
            return JsonResponse({"status":"error","msg":"Invalid tanggal"},status=400)

         # Cek jenis piutang
        if not jenis_piutang_db.objects.using(r.session["ccabang"]).filter(pk=int(jenis)).exists():
            return JsonResponse({"status":"error","msg":"Invalid jenis piutang"},status=400)

        # Jika piutang pegawai sudah ada maka update, jika tidak buat baru
        piutang = temporary_piutang_db.objects.using(r.session["ccabang"]).filter(pegawai_id=int(pegawai),jenis_piutang_id=int(jenis))
        if piutang.exists():
            return JsonResponse({'status':'error','msg':"Data piutang pegawai dengan jenis tersebut sebelumnya belum diposting. Silahkan posting atau hapus terlebih dahulu "},status=400)
        else:
            with transaction.atomic(using=r.session["ccabang"]):
                try:
                    # Cek pegawai
                    pgw = pegawai_db.objects.using(r.session["ccabang"]).filter(pk=int(pegawai))
                    if not pgw.exists():
                        raise Exception("Invalid Pegawai")
                    
                    # Cek jika pegawai ditanggal tersebut ada transaksi maka return error
                    if transaksi_db.objects.using(r.session["ccabang"]).filter(tgl=tanggal,pegawai_id=int(pegawai)).exists():
                        raise Exception("Ditanggal tersebut sudah ada transaksi piutang")
                    
                   

                    # Convert semua nilai ke integer dan insert data baru dengan cabang yang sesuai
                    nilai = int(nilai)
                    potongan = int(potongan)

                    if potongan > nilai:
                        raise Exception("Potongan lebih besar dari piutang")
                    
                    temporary_piutang_db(
                        tgl=tanggal,
                        pegawai_id=int(pegawai),
                        piutang=nilai,
                        pot_piutang=potongan,
                        jenis_piutang_id=int(jenis),
                        add_by=username
                    ).save(using=r.session["ccabang"])
                    count = temporary_piutang_db.objects.using(r.session["ccabang"]).all().aggregate(count=Count("id"))
                    return JsonResponse({"status":"success","msg":"Success add a piutang","data":{'count':count["count"]}})    
                except Exception as e:
                    transaction.set_rollback(True,using=r.session["ccabang"])
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    msg = e.args[0] if e.args is not None else "Terjadi kesalahan"
                    return JsonResponse({"status":"error","msg":msg},status=400)
        
@authorization(["root","it"])
def tbh_piutang_json(r):
    # Pastikan request dari Ajax
    if r.headers["X-Requested-With"] == 'XMLHttpRequest':
        username = r.session["user"]["nama"]
        # Ambil semua id yang dikirim
        ids = r.POST.getlist("id[]")
        print(ids)
        # Looping id
        for id in ids:
            # Memulai transaksi databse
            with transaction.atomic(using=r.session["ccabang"]):
                try:
                    # Cek jika id tidak ada maka lanjut ke looping berikutnya
                    if not temporary_piutang_db.objects.using(r.session["ccabang"]).filter(pk=int(id)):
                        continue

                    # Ambil data temporary
                    temp = temporary_piutang_db.objects.select_related("jenis_piutang").using(r.session["ccabang"]).get(pk=int(id))
                    
                    # Cek jika piutang dengan pegawai id tidak ada maka akan ditambahkan, jika ada maka akan di update
                    if not piutang_db.objects.using(r.session["ccabang"]).filter(pegawai_id=int(temp.pegawai_id)).exists():
                        # Simpan data temporary ke dalam piutang dan hapus data temporary tersebut
                        piutang_db(
                            pegawai_id=temp.pegawai_id,
                            piutang=temp.piutang,
                            pot_piutang=temp.pot_piutang,
                            pemutihan =0,
                            add_by=username
                        ).save(using=r.session["ccabang"])
                        jenis = jenis_transaksi_db.objects.using(r.session["ccabang"]).filter(jenis_transaksi__iregex=r'(saldo awal)').last()
                        if jenis is None:
                            raise Exception("Jenis saldo awal tidak ada")
                        temporary_piutang_db.objects.using(r.session["ccabang"]).filter(pk=int(id)).delete()
                        transaksi_db(
                            tgl=temp.tgl,
                            pegawai_id=temp.pegawai_id,
                            nilai=temp.piutang,
                            jenis_transaksi_id=jenis.pk
                        ).save(using=r.session["ccabang"])
                    else:
                        # Ambil piutang dan lock data tersebut
                        piutang = piutang_db.objects.select_for_update().using(r.session["ccabang"]).get(pegawai_id=int(temp.pegawai_id))

                        # Update piutang
                        totalPiutang = int(temp.piutang) + int(piutang.piutang)
                        piutang.piutang = totalPiutang
                        piutang.pot_piutang = temp.pot_piutang
                        piutang.edit_by = username
                        piutang.save(using=r.session["ccabang"])

                        temporary_piutang_db.objects.using(r.session["ccabang"]).filter(pk=int(id)).delete()
                        # Simpan transaksi ke dalam database transaksi
                        transaksi_db(
                            tgl=temp.tgl,
                            pegawai_id=temp.pegawai_id,
                            nilai=temp.piutang,
                            jenis_transaksi_id=temp.jenis_piutang.jenis_transaksi_id
                        ).save(using=r.session["ccabang"])


                except Exception as e:
                    transaction.set_rollback(True,using=r.session["ccabang"])
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    msg = e.args[0] if e.args is not None else "Terjadi kesalahan"
                    return JsonResponse({"status":"error","msg":msg},status=400)
                
        count = temporary_piutang_db.objects.using(r.session["ccabang"]).all().aggregate(count=Count("id"))
        return JsonResponse({"status":"success","msg":"Berhasil posting piutang","count":count["count"]},status=201)
    else:
        return JsonResponse({"status":"error","msg":"Not Found"},status=404)


@authorization(["root","it"])
def post_piutang_json(r):
    # Pastikan request dari Ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        data = []

        data = []
        temporary = temporary_piutang_db.objects.select_related("pegawai","jenis_piutang","jenis_piutang__jenis_transaksi").using(r.session["ccabang"]).all()
        # Jika belum ambil semua data dari table temporary
        for temp in temporary:
            obj = {
                "id":temp.pk,
                "tanggal":str(temp.tgl),
                "pegawai":temp.pegawai.nama,
                "pegawai_id":temp.pegawai_id,
                "piutang":temp.piutang,
                "pot_piutang":temp.pot_piutang,
                "jenis_piutang":temp.jenis_piutang.jenis_transaksi.jenis_transaksi,
                "jenis_id":temp.jenis_piutang_id,
            }
            data.append(obj)

        return JsonResponse({"status":"success","msg":"Berhasil ambil data temporary","data":data},status=200)
    else:
        return JsonResponse({"status":"error","msg":"Not Found"},status=404)
    

@authorization(["root","it"])
def edit_piutang_json(r):

    # Memastikan bahwa request dari ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":        
        # Ambil data dari body request
        id = r.POST.get("id")
        tanggal = r.POST.get("tanggal")
        pegawai = r.POST.get("pegawai")
        jenis = r.POST.get("jenis")
        nilai = r.POST.get("nilai")
        pot = r.POST.get("pot")
        try:
            # Cek jika salah satunya kosong
            if tanggal is None or pegawai is None or jenis is None or nilai is None or pot is None:
                return JsonResponse({"status":"error","msg":"Form tidak boleh kosong"},status=400)
            
            # Convert pegawai, jenis, nilai, dan pot ke integer
            id = int(id)
            pegawai = int(pegawai)
            jenis = int(jenis)
            nilai = int(nilai)
            pot = int(pot)

            # Convert tanggal menjadi format YYYY-MM-DD
            try:
                tanggal = datetime.strptime(tanggal,"%Y-%m-%d")
            except Exception as e:
                return JsonResponse({"status":"error","msg":"Invalid tanggal"},status=400)
            
            # Cek jika pegawai tidak ada maka return error
            if not pegawai_db.objects.using(r.session["ccabang"]).filter(pk=int(pegawai)).exists():
                return JsonResponse({"status":"error","msg":"Pegawai tidak ada"},status=400)
            
            # Cek jika pegawai ditanggal tersebut ada transaksi maka return error
            if transaksi_db.objects.using(r.session["ccabang"]).filter(tgl=tanggal,pegawai_id=int(pegawai)).exists():
                return JsonResponse({"status":"error",'msg':"Ditanggal tersebut sudah ada transaksi piutang"},status=400)

            # Cek jika jenis piutang tidak ada maka return error
            if not jenis_piutang_db.objects.using(r.session["ccabang"]).filter(pk=int(jenis)).exists():
                return JsonResponse({"status":"error",'msg':"Jenis tidak ada"},status=400)
            
            # Cek jika temporary tidak ada
            if not temporary_piutang_db.objects.using(r.session["ccabang"]).filter(pk=int(id)).exists():
                return JsonResponse({"status":"error","msg":"Temporary tidak ada"},status=400)

            # Memulai transaksi database
            with transaction.atomic(using=r.session["ccabang"]):
                try:
                    # Ambil data terakhir dari id 
                    temp = temporary_piutang_db.objects.select_for_update().using(r.session["ccabang"]).filter(pk=int(id)).last()
                    
                    if pot > int(temp.pot_piutang):
                        raise Exception("Potongan lebih besar dari piutang")

                    # Cek jika data tidak ada kembalikan error
                    if temp is None:
                        raise Exception("Data tidak ada")
                    
                    # Update Data
                    temp.tgl = tanggal
                    temp.pegawai_id=pegawai
                    temp.piutang = nilai
                    temp.pot_piutang = pot
                    temp.jenis_piutang_id=jenis
                    temp.save(using=r.session["ccabang"])

                    # Update data redis
                    return JsonResponse({"status":"success","msg":"Berhasil edit temporary"},status=200)
                except Exception as e:
                    transaction.set_rollback(True,using=r.session["ccabang"])
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    msg = e.args[0] if e.args is not None else "Terjadi kesalahan"
                    return JsonResponse({"status":"error",'msg':msg},status=400)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            return JsonResponse({"status":"error","msg":"Terjadi kesalahan"},status=400)


@authorization(["root","it"])
def delete_piutang_json(r):

    # Memastikan bahwa request dari ajax
        if r.headers["X-Requested-With"] == 'XMLHttpRequest':
            # Ambil data dari body request
            id = r.POST.get("id")
            try:
                # Convert id ke integer
                id = int(id)

                # Hapus jika ada kalo ga ada ya udah
                temporary_piutang_db.objects.using(r.session["ccabang"]).filter(pk=int(id)).delete()
                count = temporary_piutang_db.objects.using(r.session["ccabang"]).all().aggregate(count=Count("id"))
                return JsonResponse({"status":'success',"msg":"Berhasil hapus datas","count":count},status=200)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                return JsonResponse({'status':'error',"msg":"Terjadi kesalahan"},status=400)
            
@authorization(["root","it"])
def edit_potongan_json(r):
    # Memastikan bahwa request dari ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        id = r.POST.get("id")
        pot = r.POST.get("pot")

        if id is None or pot is None:
            return JsonResponse({'status':"error","msg":"Lengkapi form yang ada"},status=400)
        with transaction.atomic(using=r.session["ccabang"]):
            try:
                # Convert id dan potongan ke integer
                id = int(id)
                pot = int(pot)

                # Memulai transaksi database
                # Ambil data piutang sesuai denagn id
                piutang = piutang_db.objects.select_for_update().using(r.session["ccabang"]).filter(pk=int(id)).last()
                
                # Cek jika potongan melebihi piutang return error
                if pot > int(piutang.piutang):
                    raise Exception("Potongan lebih besar dari piutang")
                # Cek apakah data piutang ada, jika tidak maka kembalikan error
                if piutang is None:
                    raise Exception("Data tidak ada")
                
                # Update data
                piutang.pot_piutang = pot
                piutang.save(using=r.session["ccabang"])
                # Updata data di redis
                return JsonResponse({"status":"success","msg":"Berhasil edit potongan piutang"},status=200)
            except Exception as e:
                transaction.set_rollback(True,using=r.session["ccabang"])
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                msg = e.args[0] if e.args is not None else "Terjadi kesalahan"
                return JsonResponse({"status":'error',"msg":msg},status=400)
        

@authorization(["root","it"])
def detail_piutang_json(r):
    # Memastikan request hanya dari ajax
    if r.headers["X-Requested-With"] == 'XMLHttpRequest':
        
        # Mengambil data dari body request
        idp = r.POST.get("idp")
        try:
            # Convert idp ke integer
            idp = int(idp)

            data = []
            transaksi = transaksi_db.objects.select_related("pegawai","jenis_transaksi","kode_piutang").using(r.session["ccabang"]).filter(pegawai_id=int(idp))
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
            
            return JsonResponse({"status":'success',"msg":"Berhasil ambil data transaksi","data":data},status=200)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            return JsonResponse({"status":"error","msg":"Terjadi kesalahan"},status=400)
        

@authorization(["root","it"])
def edit_detail_json(r):
    # Memastikan request hanya dari ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        # Ambil data dari body request
        id = r.POST.get("id")
        nilai = r.POST.get("nilai")

        if id is None or nilai is None:
            return JsonResponse({'status':'error',"msg":"Lengkapi form yang ada"},status=400)
        try:
            id = int(id)
            nilai = int(nilai)
            # Jika transaksi tidak ada maka return error
            if not transaksi_db.objects.using(r.session["ccabang"]).filter(pk=int(id)).exists():
                return JsonResponse({"status":"error","msg":"Data tidak ada"},status=400)
            
            # Memulai transaksi database
            with transaction.atomic(using=r.session["ccabang"]):
                try:
                    # Ambil transaksi
                    trans = transaksi_db.objects.select_related("pegawai").select_for_update().using(r.session["ccabang"]).filter(pk=int(id)).last()

                    # Ambil data pegawai dati pegawai transaksi
                    piutang = piutang_db.objects.select_for_update().using(r.session["ccabang"]).filter(pegawai_id=trans.pegawai_id).last()

                    # Cek jika piutang tidak ada maka return error
                    if piutang is None:
                        raise Exception("Pegawai tidak ada")
                    
                    # Cek jika jenis transaksi "ketemu" maka kurangi piutang, selain itu tambah piutang
                    if re.search("ketemu",trans.jenis_transaksi.jenis_transaksi,re.IGNORECASE):
                        piutang.piutang = piutang.piutang + (trans.nilai - nilai)
                    else:
                        piutang.piutang = piutang.piutang - ((trans.nilai - nilai))
                    piutang.save(using=r.session["ccabang"])

                    # Update transaksi nilai 
                    trans.nilai = nilai
                    trans.save(using=r.session["ccabang"])

                    # Update data transaksi di redis
                    return JsonResponse({"status":'success',"msg":"Berhasil edit data"},status=200)
                except Exception as e:
                    transaction.set_rollback(True,using=r.session["ccabang"])
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    msg = e.args[0] if e.args is not None else "Terjadi kesalahan"
                    return JsonResponse({"status":'error',"msg":msg},status=400)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            return JsonResponse({"status":"error","msg":"Terjadi kesalahan"},status=400)
        


@authorization(["root","it"])
def pelunasan_json(r):
    # Memastikan request hanya dari ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":

        # Ambil data dari body request
        id = r.POST.get("id")
        idj = r.POST.get("jpembayaran")
        total = r.POST.get("tpembayaran")

        if id is None or idj is None or total is None:
            return JsonResponse({"status":'error',"msg":"Lengkapi form yang ada"},status=400)
        try:
            # Convert data ke integer
            id = int(id)
            total = int(total)
            idj = int(idj)
            
            # Ambil tanggal hari ini
            today = datetime.now().date()

            # Jika piutang tidak ada maka return error
            if not piutang_db.objects.using(r.session["ccabang"]).filter(pk=int(id)).exists():
                return JsonResponse({"status":'error',"msg":"Data piutang tidak ada"},status=400)
            
            # Jikta jenis transaksi tidak ada maka return error
            if not jenis_transaksi_db.objects.using(r.session["ccabang"]).filter(pk=int(idj)).exists():
                return JsonResponse({'status':'erorr',"msg":"Data jenis transaksi tidak ada"},status=400)
            with transaction.atomic(using=r.session["ccabang"]):
                try:
                    # Ambil piutang lalu lock data
                    piutang = piutang_db.objects.select_for_update().using(r.session["ccabang"]).filter(pk=int(id)).last()
                    totalPiutang = int(piutang.piutang)

                    # Ambil jenis transaksi
                    jenis = jenis_transaksi_db.objects.using(r.session['ccabang']).filter(pk=int(idj)).last()

                    # Cek jika memang yang dipilih adalah pemutihan
                    if re.search('pemutihan',jenis.jenis_transaksi,re.IGNORECASE):
                        piutang.pemutihan = 1
                        piutang.pot_piutang = 0
                        piutang.piutang = 0
                        piutang.save(using=r.session["ccabang"])

                        # Tambah transaksi dengan jenis transaksi pemutihan ditanggal hari ini
                        transaksi_db(
                            tgl=today,
                            pegawai_id=piutang.pegawai_id,
                            nilai=total,
                            jenis_transaksi_id=jenis.pk  
                        ).save(using=r.session["ccabang"])
                        return JsonResponse({"status":"success","msg":"Berhasil melakukan pelunasan"},status=200)

                    # Jika total tidak sama dengan total piutang maka return error
                    if total != totalPiutang:
                        raise Exception("Total pembayaran harus sama dengan piutang yang ada")
                    
                    # Set piutang jadi 0
                    piutang.piutang = 0
                    piutang.pot_piutang = 0
                    piutang.save(using=r.session["ccabang"])
                    
                    # Tambahkan transaksi dengan jenis transksi selain pemutihan ditanggal hari ini
                    transaksi_db(
                        tgl=today,
                        pegawai_id=piutang.pegawai_id,
                        nilai=total,
                        jenis_transaksi_id=jenis.pk  
                    ).save(using=r.session["ccabang"])
                    return JsonResponse({"status":"success","msg":"Berhasil melakukan pelunasan"},status=200)
                except Exception as e:
                    transaction.set_rollback(True,using=r.session["ccabang"])
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    msg = e.args[0] if e.args is not None else "Terjadi kesalahan"
                    return JsonResponse({"status":'error',"msg":msg},status=400)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            return JsonResponse({"status":"error","msg":"Terjadi Kesalahan"},status=400)
        

@authorization(["root","it"])
def tketemu_keliru(r):
    # Memastikan request hanya dari ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":

        # Ambil data dari body request
        idp = r.POST.get("idp")
        ketemu = r.POST.get("ketemu")

        # Ambil tanggal sekarang
        today = datetime.today().date()
        try:

            if idp is None or ketemu is None:
                return JsonResponse({"status":"error","msg":"Lengkapi data yang ada"},status=400)
            # Convert data ke integer:
            idp = int(idp)
            ketemu = int(ketemu)

            # Cek jika pegawai tidak ada maka return error
            if not pegawai_db.objects.using(r.session["ccabang"]).filter(pk=idp).exists():
                return JsonResponse({"status":"error","msg":"Pegawai tidak ada"},status=400)
            
            with transaction.atomic(using=r.session["ccabang"]):
                try:
                    # Ambil jenis transaksi "ketemu"
                    jenis = jenis_transaksi_db.objects.using(r.session["ccabang"]).filter(jenis_transaksi__iregex=r'ketemu').last()
                    if jenis is None:
                        raise Exception("Jenis transaksi 'ketemu' tidak ada") 

                    # Ambil data piutang
                    piutang = piutang_db.objects.select_for_update().using(r.session["ccabang"]).filter(pegawai_id=idp).last()
                    
                    # Jika piutang tidak ada maka return error
                    if piutang is None:
                        raise Exception("Piutang tidak ada")
                    
                    # Cek jika piutang sama atau kurang dari 0 maka return error
                    if piutang.piutang <= 0:
                        raise Exception("Pegawai tersebut tidak memiliki piutang")
                    
                    # Cek jika piutang lebih kecil dari ketemu maka return error
                    if piutang.piutang < ketemu:
                        raise Exception("Piutang lebih kecil dari ketemu")
                    
                        
                    total = piutang.piutang - ketemu
                    piutang.piutang = total

                    piutang.save(using=r.session["ccabang"])

                    # Cek jika tidak ada ketemu maka bikin baru
                    if not ketemu_db.objects.using(r.session["ccabang"]).filter(pegawai_id=idp).exists():
                        ketemu_db(
                            pegawai_id=idp,
                            ketemu=ketemu
                        ).save(using=r.session["ccabang"])

                    # Jika sudah ada maka update ketemu
                    else:
                        ketemudb = ketemu_db.objects.select_for_update().using(r.session["ccabang"]).filter(pegawai_id=idp).last()
                        ketemudb.ketemu = ketemudb.ketemu + ketemu
                        ketemudb.save(using=r.session["ccabang"])

                    # Insert transaksi dengan jenis transaksi ketemu
                    transaksi_db(
                        tgl=today,
                        pegawai_id=idp,
                        nilai=ketemu,
                        jenis_transaksi_id=jenis.pk
                    ).save(using=r.session["ccabang"])

                    # Set data redis transaksi
                    return JsonResponse({"status":'success',"msg":"Berhasil tambah ketemu"},status=201)
                except Exception as e:
                    transaction.set_rollback(True,using=r.session['ccabang'])
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    msg = e.args[0] if e.args is not None else "Terjadi kesalahan"
                    return JsonResponse({'status':"error","msg":msg},status=400)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            return JsonResponse({'status':"error","msg":"Terjadi kesalahan"},status=400)