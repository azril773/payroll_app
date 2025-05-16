from ..lib import *

@authorization(["root","it"])
def pot_absensi(r):
    id_user = r.session["user"]["id"]
    status =status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').all()
    return render(r,'pengaturan/pot_absensi.html',{
        "status":status,
        "staff":r.session["user"]["admin"],
    })

@authorization(["root","it"])
def pot_absensi_json(r):
    if r.headers["X-Requested-With"] == 'XMLHttpRequest':
        potongan = pot_absensi_db.objects.using(r.session["ccabang"]).all()

        data = []
        for pot in potongan:
            obj = {
                "id":pot.pk,
                "potongan":pot.potongan
            }
            data.append(obj)

        return JsonResponse({"status":"success","msg":"berhasil ambil data potongan","data":data},status=200)
    
@authorization(["root","it"])
def edit_pot_json(r):
    if r.headers["X-Requested-With"] == 'XMLHttpRequest':
        id = r.POST.get("id")
        pot = r.POST.get("pot")
        if pot is None or id is None:
            return JsonResponse({"status":'error',"msg":"Harap isi form dengan lengkap"},status=400)
        try:
            id = int(id)
            pot = int(pot)

            with transaction.atomic(using=r.session["ccabang"]):
                potongan = pot_absensi_db.objects.select_for_update().using(r.session["ccabang"]).filter(pk=id).last()
                if potongan is not None:
                    potongan.potongan = pot
                    potongan.save(using=r.session["ccabang"])
                    return JsonResponse({"status":"error","msg":"berhasil update potongan"},status=200)
                else:
                    return JsonResponse({"status":"error","msg":"data tidak ditemukan"},status=400)
        except Exception as e:
            return JsonResponse({"status":"error","msg":"Terjadi kesalahan"},status=400)
        
@authorization(["root","it"])
def tambah_pot_json(r):
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        pot = r.POST.get("pot")


        if pot is None:
            return JsonResponse({"status":'error',"msg":"Harap isi form dengan lengkap"},status=400)
        try:
            pot = int(pot)
            pot_absensi_db(
                potongan=pot
            ).save(using=r.session["ccabang"])
            return JsonResponse({"status":'success',"msg":"Berhasil tambah data potongan"},status=201)
        except Exception as e:
            return JsonResponse({'status':'error',"msg":"Terjadi kesalahan"},status=400)
        


@authorization(["root","it"])
def rek_sumber_dana(r):
    id_user = r.session["user"]["id"]
    status = status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').all()
    return render(r,"pengaturan/rek_sumber_dana.html",{"status":status,"staff":r.session["user"]["admin"]})



@authorization(["root","it"])
def rek_sumber_dana_json(r):
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        rekening = rekening_db.objects.using(r.session["ccabang"]).all()
        data = []
        for rek in rekening:
            obj = {
                "id":rek.pk,
                "nama_rek":rek.nama_rekening,
                "no_rek":rek.norek,
                "atas_nama":rek.atas_nama,
                "bank":rek.bank,
                "status_bpjs": 'BPJS' if rek.bpjs == 1 else "Non BPJS",
                "bpjs": rek.bpjs,
                "email":rek.email
            }
            data.append(obj)

        return JsonResponse({'status':'error',"msg":"berhasil ambil data rekening sumber dana","data":data})
    
@authorization(["root","it"])
def tambah_rek_sumber_dana_json(r):
    # Memastikan request hanya dari ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":

        # Mengambil data dari body request
        nama = r.POST.get("nama_rek")
        norek = r.POST.get("norek")
        atas_nama = r.POST.get("atas_nama")
        bank = r.POST.get("bank")
        bpjs = r.POST.get("bpjs")
        email = r.POST.get("email")
        username = r.session["user"]["nama"]

        # cek jika salah satunya tidak ada maka return error
        if nama is None or norek is None or atas_nama is None or bank is None or email is None:
            return JsonResponse({'status':'error',"msg":"Harap isi form dengan lengkap"},status=400)

        try:
            # jika norek bukan numeric maka return error
            if not str(norek).isdigit():
                return JsonResponse({"status":"error","msg":"No Rekening harus berupa angka"},status=400)
            
            # jika format email salah maka return error
            if not re.match("[a-zA-Z0-9.]+@(gmail\.com|yahoo\.com)",email):
                return JsonResponse({"status":"error","msg":"Format email salah, gunakan @gmail.com atau @yahoo.com"},status=400)
            
            # jika rekening sudah ada maka return error
            if rekening_db.objects.using(r.session["ccabang"]).filter(nama_rekening=nama).exists():
                return JsonResponse({"status":'error',"msg":"Nama rekening sudah ada"},status=400)
            
            # jika atas nama sudah ada maka return error
            if rekening_db.objects.using(r.session["ccabang"]).filter(atas_nama=atas_nama).exists():
                return JsonResponse({"status":"error","msg":"Atas nama tersebut sudah ada"},status=400)
            
            # jika email sudah ada maka return error
            if rekening_db.objects.using(r.session["ccabang"]).filter(email=email).exists():
                return JsonResponse({"status":'error',"msg":"Email sudah ada"},status=400)
            
            # jika norek sudah ada maka return error
            
            if rekening_db.objects.using(r.session["ccabang"]).filter(norek=norek).exists():
                return JsonResponse({"status":'error',"msg":"No Rekening sudah ada"},status=400)

            # simpan data ke rekening db
            rekening_db.objects.using(r.session["ccabang"]).create(
                nama_rekening=nama,
                bank=bank,
                norek=norek,
                atas_nama=atas_nama,
                # alias=
                bpjs=bpjs,
                email=email,
                add_by=username
            )
            return JsonResponse({"status":'success',"msg":"Rekening berhasil disimpan"},status=201)
        except Exception as e:
            print(e)
            return JsonResponse({"status":"error","msg":"Terjadi Kesalahan"},status=400)
        

def edit_rek_sumber_dana_json(r):
    # Memastikan request hanya dari ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":

        # Mengambil data dari body request
        nama = r.POST.get("nama_rek")
        norek = r.POST.get("norek")
        atas_nama = r.POST.get("atas_nama")
        bank = r.POST.get("bank")
        bpjs = r.POST.get("bpjs")
        email = r.POST.get("email")
        id = r.POST.get("id")
        username = r.session["user"]["nama"]

        # cek jika salah satunya tidak ada maka return error
        if nama is None or norek is None or atas_nama is None or bank is None or email is None or id is None:
            return JsonResponse({'status':'error',"msg":"Harap isi form dengan lengkap"},status=400)
        try:
            # convert type id ke integer
            id = int(id)

            # cek jika norek bukan numeric maka return error
            if not str(norek).isdigit():
                return JsonResponse({"status":'error',"msg":"No Rekening harus berupa angka"},status=400)

            # jika format email salah maka return error
            if not re.match("[a-zA-Z0-9.]+@(gmail\.com|yahoo\.com)",email):
                return JsonResponse({"status":"error","msg":"Format email salah, gunakan @gmail.com atau @yahoo.com"},status=400)
            
            # jika rekening sudah ada maka return error
            if rekening_db.objects.using(r.session["ccabang"]).filter(~Q(pk=id),nama_rekening=nama).exists():
                return JsonResponse({"status":'error',"msg":"Nama rekening sudah ada"},status=400)
            
            # jika atas nama sudah ada maka return error
            if rekening_db.objects.using(r.session["ccabang"]).filter(~Q(pk=id),atas_nama=atas_nama).exists():
                return JsonResponse({"status":"error","msg":"Atas nama tersebut sudah ada"},status=400)
            
            # jika email sudah ada maka return error
            if rekening_db.objects.using(r.session["ccabang"]).filter(~Q(pk=id),email=email).exists():
                return JsonResponse({"status":'error',"msg":"Email sudah ada"},status=400)
            
            # jika norek sudah ada maka return error
            
            if rekening_db.objects.using(r.session["ccabang"]).filter(~Q(pk=id),norek=norek).exists():
                return JsonResponse({"status":'error',"msg":"No Rekening sudah ada"},status=400)
            
            rekening_db.objects.using(r.session["ccabang"]).filter(id=id).update(
                nama_rekening=nama,
                bank=bank,
                norek=norek,
                atas_nama=atas_nama,
                # alias=
                bpjs=bpjs,
                email=email,
                edit_by=username
            )
            return JsonResponse({"status":'error',"msg":"Rekening berhasil di update"},status=200)
        except Exception as e:
            return JsonResponse({"status":'error',"msg":"Terjadi kesalahan"},status=400)
        

@authorization(["root","it"])
def delete_rek_sumber_dana_json(r):
    if r.headers["X-Requested-With"] == "XMLHttpRequest":

        # Mengambil data dari body request
        id = r.POST.get("id")
        username = r.session["user"]["nama"]

        try:
            # convert type id ke integer
            id = int(id)
            rekening_db.objects.using(r.session["ccabang"]).filter(id=id).delete()
            return JsonResponse({"status":'error',"msg":"Rekening berhasil di hapus"},status=200)
        except Exception as e:
            print(e.args[0])
            if re.search('protected',e.args[0],re.IGNORECASE):
                return JsonResponse({"status":'error',"msg":"Rekening sedang digunakan oleh data lain."},status=400)
            return JsonResponse({"status":'error',"msg":"Terjadi kesalahan."},status=400)


@authorization(["root","it"])
def ttrans(r):
    id_user = r.session["user"]["id"]
    status = status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').all()
    return render(r,"pengaturan/ttrans.html",{"status":status,"staff":r.session["user"]["admin"]})

@authorization(["root","it"])
def ttrans_json(r):
    if r.headers["X-Requested-With"] == 'XMLHttpRequest':
        ttrans = ttrans_db.objects.using(r.session["ccabang"]).all()

        data = []
        for t in ttrans:
            obj = {
                "id":t.pk,
                "jenis":t.jenis_transfer,
                "tanggal":t.tanggal_transfer
            }
            data.append(obj)

        return JsonResponse({"status":"success","msg":"berhasil ambil data potongan","data":data},status=200)
    
@authorization(["root","it"])
def tambah_ttrans_json(r):
    # Memastikan request hanya dari ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":

        # Mengambil data dari body request
        jenis = r.POST.get("jenis")
        tanggal = r.POST.get("tanggal")
        username = r.session["user"]["nama"]

        # cek jika salah satunya tidak ada maka return error
        if jenis is None or tanggal is None:
            return JsonResponse({'status':'error',"msg":"Harap isi form dengan lengkap"},status=400)

        try:
            # ubah format tanggal
            tanggal = datetime.strptime(tanggal,"%Y-%m-%d")
            
            # Cek jika jenis sudah ada maka return error
            if ttrans_db.objects.using(r.session["ccabang"]).filter(jenis_transfer=jenis).exists():
                return JsonResponse({"status":"error","msg":"Jenis transfer sudah ada"},status=400)
            
            # simpan data ke rekening db
            ttrans_db.objects.using(r.session["ccabang"]).create(
                jenis_transfer=jenis,
                tanggal_transfer=tanggal
            )
            return JsonResponse({"status":'success',"msg":"Rekening berhasil disimpan"},status=201)
        except Exception as e:
            print(e)
            return JsonResponse({"status":"error","msg":"Terjadi Kesalahan"},status=400)

@authorization(["root","it"])
def edit_ttrans_json(r):
    # Memastikan request hanya dari ajax
    if r.headers["X-Requested-With"] == "XMLHttpRequest":

        # Mengambil data dari body request
        id = r.POST.get("id")
        jenis = r.POST.get("jenis")
        tanggal = r.POST.get("tanggal")
        username = r.session["user"]["nama"]

        # cek jika salah satunya tidak ada maka return error
        if jenis is None or tanggal is None or id is None:
            return JsonResponse({'status':'error',"msg":"Harap isi form dengan lengkap"},status=400)

        try:
            # convert id ke integer
            id = int(id)
             # Cek jika jenis sudah ada di selain id maka return error
            if ttrans_db.objects.using(r.session["ccabang"]).filter(~Q(pk=id),jenis_transfer=jenis).exists():
                return JsonResponse({"status":"error","msg":"Jenis transfer sudah ada"},status=400)

            # simpan data ke rekening db
            ttrans_db.objects.using(r.session["ccabang"]).filter(pk=id).update(
                jenis_transfer=jenis,
                tanggal_transfer=tanggal
            )
            return JsonResponse({"status":'success',"msg":"Rekening berhasil diupdate"},status=201)
        except Exception as e:
            print(e)
            return JsonResponse({"status":"error","msg":"Terjadi Kesalahan"},status=400)
        


@authorization(["root","it"])
def akses(r):
    pass


@authorization(["root","it"])
def delete_ttrans_json(r):
    if r.headers["X-Requested-With"] == "XMLHttpRequest":
        id = r.POST.get("id")

        try:
            id = int(id)
            ttrans_db.objects.using(r.session["ccabang"]).filter(pk=id).delete()
            return JsonResponse({"status":'success',"msg":"Data berhasil dihapus"},status=200)
        except Exception as e:
            return JsonResponse({"status":"error","msg":"Terjadi kesalahan"},status=400)
        

@authorization(["root","it"])
def akses(r):
    id_user = r.session["user"]["id"]
    status = status_pegawai_payroll_db.objects.using(f'p{r.session["ccabang"]}').all()
    user = user_db.objects.all()
    return render(r,"pengaturan/akses.html",{"status":status,"staff":r.session["user"]["admin"],"user":user})

@authorization(["root","it"])
def takses(r):
    if r.method == "POST":
        user = r.POST.get("user")
        akses = r.POST.get("akses")

        if user == "" or akses == "":
            messages.error(r,"Harap lengkapi form yang ada")
            return redirect("akses")

        ak = akses_db.objects.filter(user_id=user).last()
        if ak is not None:
            ak.akses = akses
            ak.save()
        else:
            akses_db(user_id=user,akses=akses).save()

        messages.success(r,"Berhasil memberikan akses")
        return redirect("akses")