from django.db import models
from django.contrib.auth.models import User
import datetime
# Create your models here.

# Kode Piutang
class kode_piutang_db(models.Model):
    kode = models.CharField(max_length=50)
    nama_kode = models.CharField(max_length=50)
    inisial = models.CharField(max_length=50, null=True, blank=True)
    add_by = models.CharField(max_length=50, null=True, blank=True)
    add_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    edit_by = models.CharField(max_length=50, null=True, blank=True)
    edit_date = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.nama_kode

    class Meta:
        verbose_name = "Kode Piutang"
        verbose_name_plural = "Kode Piutang"


# no dokumen
class no_dokumen_db(models.Model):
    kode_piutang = models.ForeignKey(kode_piutang_db, on_delete=models.CASCADE, null=True)
    nodok = models.IntegerField(default=0)


# jenis bpjs
class jbpjs_db(models.Model):
    jenis = models.CharField(max_length=50, null=True)
    tanggungan_perusahaan = models.IntegerField(default=0)

    add_by = models.CharField(max_length=50, null=True, blank=True)
    add_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    edit_by = models.CharField(max_length=50, null=True, blank=True)
    edit_date = models.DateTimeField(auto_now=True, null=True, blank=True)





################################## Payroll Models ##################################

class status_pegawai_db(models.Model):
    status = models.CharField(max_length=100)

    def __str__(self):
        return self.status

    class Meta:
        verbose_name="Status Pegawai"    
        verbose_name_plural="Status Pegawai"    

class divisi_db(models.Model):
    divisi = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.divisi
    
    class Meta:
        verbose_name = "Divisi"
        verbose_name_plural = "Divisi"


class counter_db(models.Model):
    counter = models.CharField(max_length=100)

    def __str__(self):
        return self.counter

    class Meta:
        verbose_name = 'Counter'
        verbose_name_plural = 'Counter'   

# rekening sumber dana
class rekening_db(models.Model):
    nama_rekening = models.CharField(max_length=100, null=True)
    bank = models.CharField(max_length=100, null=True)
    norek = models.CharField(max_length=100, null=True)
    atas_nama = models.CharField(max_length=100, null=True)
    alias = models.CharField(max_length=100, null=True)
    bpjs = models.IntegerField()
    email = models.CharField(max_length=100, null=True)
    add_by = models.CharField(max_length=50, null=True, blank=True)
    add_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    edit_by = models.CharField(max_length=50, null=True, blank=True)
    edit_date = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.alias

    class Meta:
        verbose_name = "Rekening sumber dana"
        verbose_name_plural = "Rekening sumber dana"
pilihan_pengelola = (("Owner", "Owner"),("HRD", "HRD"), ("Lainnya", "Lainnya"))         

class pegawai_db(models.Model):
    nama = models.CharField(max_length=200, null=True)
    userid = models.CharField(max_length=100, null=True)
    gender = models.CharField(max_length=50, null=True)
    tgl_masuk = models.DateField(null=True)
    masa_kerja = models.IntegerField(null=True)
    status = models.ForeignKey(status_pegawai_db,on_delete=models.CASCADE,null=True)
    nik = models.CharField(max_length=100, null=True)
    divisi = models.ForeignKey(divisi_db,on_delete=models.CASCADE,null=True)
    # counter_id = models.IntegerField(null=True)


    gaji = models.IntegerField(null=True)
    no_rekening = models.CharField(max_length=50, null=True, blank=True)
    no_bpjs_ks = models.CharField(max_length=50, null=True, blank=True)
    no_bpjs_tk = models.CharField(max_length=50, null=True, blank=True)
    rek_sd = models.ForeignKey(rekening_db, on_delete=models.PROTECT, null=True)
    payroll_by = models.CharField(max_length=50, choices=pilihan_pengelola, default='HRD')
    t_jabatan = models.IntegerField(default=0,null=True)
    t_tetap = models.IntegerField(default=0,null=True)
    t_c = models.CharField(max_length=50, default='transfer',null=True)

    ks_premi = models.IntegerField(default=0)
    tk_premi = models.IntegerField(default=0)

    aktif = models.IntegerField(null=True)
    status_payroll = models.IntegerField(null=True, default=0)

    add_by = models.CharField(max_length=100, null=True, blank=True)
    edit_by = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update_at = models.DateTimeField(auto_now=True, null=True)


class cabang_db(models.Model):
    cabang = models.CharField(max_length=100,null=False)

    def __str__(self) -> str:
        return self.cabang
    
    class Meta:
        verbose_name = "Cabang"
        verbose_name_plural = "Cabang"


class akses_cabang_db(models.Model):
    user = models.ForeignKey(User,on_delete=models.PROTECT)
    cabang = models.ForeignKey(cabang_db,on_delete=models.CASCADE)
    
    add_by = models.CharField(max_length=200,null=True)
    edit_by = models.CharField(max_length=200,null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    update_at = models.DateTimeField(null=True)

    def __str__(self) -> str:
        return self.user.username
    

pilihan_akses = (("root", "root"),("admin", "admin"),("it", "it"),("user", "user"),("tamu", "tamu"),) 

class akses_db(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    akses = models.CharField(max_length=100, choices=pilihan_akses, default="user")

    def __int__(self):
        return self.user


class akses_divisi_db(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    divisi = models.ForeignKey(divisi_db, on_delete=models.CASCADE)

    def __int__(self):
        return self.user 
    

################################## Payroll Models ##################################
class gaji_db(models.Model):
    pegawai = models.ForeignKey(pegawai_db,on_delete=models.PROTECT,null=True)
    status_pegawai = models.ForeignKey(status_pegawai_db,on_delete=models.PROTECT,null=False)
    periode  = models.IntegerField()
    tahun  = models.IntegerField()
    tgl_bayar = models.DateField()
    t_masakerja  = models.IntegerField()
    t_jabatan  = models.IntegerField()
    t_tetap  = models.IntegerField()
    insentif  = models.IntegerField()
    pot_hari  = models.IntegerField()
    pot_rupiah  = models.IntegerField()
    pot_piutang  = models.IntegerField()
    bpjs  = models.IntegerField()
    bpjs_ks  = models.IntegerField()
    bpjs_tk  = models.IntegerField()
    gaji  = models.IntegerField()
    thp  = models.IntegerField()
    gaji_cm = models.IntegerField(default=0)
    rek_sd  = models.ForeignKey(rekening_db,on_delete=models.CASCADE)
    status=models.IntegerField(default=0)
    status_pothr=models.IntegerField(default=0)
    status_potpiutang=models.IntegerField(default=0)
    status_ebpjs_tk=models.IntegerField(default=0)
    status_ebpjs_ks=models.IntegerField(default=0)
    add_by = models.CharField(max_length=50,null=True)
    edit_by = models.CharField(max_length=50,null=True)
    add_date = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    edit_date = models.DateTimeField(auto_now=True,null=True,blank=True)


jenis_choices = (("Payroll","Payroll"),("Piutang","Piutang"))
class ttrans_db(models.Model):
    jenis_transfer = models.CharField(max_length=100,choices=jenis_choices)
    tanggal_transfer = models.DateField()

    def __str__(self) -> str:
        return self.jenis_transfer

    class Meta:
        verbose_name = "Tanggal Transfer"
        verbose_name_plural = "Tanggal Transfer"

class pot_absensi_db(models.Model):
    potongan = models.IntegerField(null=True)
    add_by = models.CharField(max_length=50, null=True, blank=True)
    add_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    edit_by = models.CharField(max_length=50, null=True, blank=True)
    edit_date = models.DateTimeField(auto_now=True,null=True, blank=True)

    def __int__(self):
        return self.potongan

    class Meta:
        verbose_name = "Potongan absensi"
        verbose_name_plural = "Potongan absensi"

class data_ijin_db(models.Model):
    # nik = models.IntegerField(default=0)
    # userid = models.CharField(max_length=100, null=True)
    pegawai = models.ForeignKey(pegawai_db,on_delete=models.CASCADE)
    periode = models.IntegerField(default=0)
    tahun = models.IntegerField(null=True)
    sb = models.IntegerField(default=0, null=True)
    sdl = models.IntegerField(default=0, null=True)
    sdp = models.IntegerField(default=0, null=True)
    ijin = models.IntegerField(default=0, null=True)
    af = models.IntegerField(default=0, null=True)
    insentif = models.IntegerField(default=0, null=True)
    ket = models.TextField(null=True)
    add_by = models.CharField(max_length=50, null=True, blank=True)
    add_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    edit_by = models.CharField(max_length=50, null=True, blank=True)
    edit_date = models.DateTimeField(auto_now=True,null=True, blank=True)


# Histori rekap gaji
class histori_rekap_gaji_db(models.Model):
    pegawai = models.ForeignKey(pegawai_db,on_delete=models.CASCADE,null=True)
    nik = models.CharField(max_length=100)
    divisi = models.ForeignKey(divisi_db,on_delete=models.CASCADE,null=True)
    t_masakerja = models.IntegerField(default=0)
    t_jabatan = models.IntegerField(default=0)
    t_tetap = models.IntegerField(default=0)
    insentif = models.IntegerField(default=0)
    tgl_bayar = models.DateField(null=True, blank=True)
    gaji = models.IntegerField(default=0)
    cm = models.IntegerField(default=0)
    cm_ke = models.IntegerField(default=0)
    pot_hari = models.IntegerField(default=0)
    pot_rupiah = models.IntegerField(default=0)
    pot_piutang = models.IntegerField(default=0)
    bpjs_tk = models.IntegerField(default=0)
    bpjs_ks = models.IntegerField(default=0)
    bpjs = models.IntegerField(default=0)
    thp = models.IntegerField(default=0)
    rek_sumber = models.ForeignKey(rekening_db, on_delete=models.CASCADE, null=True)
    status = models.IntegerField(default=0)
    ket = models.TextField(null=True)
    add_by = models.CharField(max_length=50, null=True)
    add_date = models.DateTimeField(auto_now_add=True,blank=True)
    edit_by = models.CharField(max_length=50, null=True)
    edit_date = models.DateTimeField(auto_now=True,blank=True)

    def __int__(self):
        return self.pegawai

    class Meta:
        verbose_name = "Histori Rekap Gaji"
        verbose_name_plural = "Histori Rekap Gaji"


# Summary pembayaran gaji
class summary_rekap_gaji_db(models.Model):
    status_pegawai = models.ForeignKey(status_pegawai_db,on_delete=models.CASCADE,null=True)
    tgl_bayar = models.DateField(null=True, blank=True)
    total_gaji_bruto = models.IntegerField(default=0)
    total_tmasakerja = models.IntegerField(default=0)
    total_ttetap = models.IntegerField(default=0)
    total_tjabatan = models.IntegerField(default=0)
    total_insentif = models.IntegerField(default=0)
    total_pot_piutang = models.IntegerField(default=0)
    total_pot_absensi = models.IntegerField(default=0)
    total_bpjs_tk = models.IntegerField(default=0)
    total_bpjs_ks = models.IntegerField(default=0)
    total_gaji_cm = models.IntegerField(default=0)
    total_bayar_gaji = models.IntegerField(default=0)
    add_by = models.CharField(max_length=50, null=True)
    edit_by = models.CharField(max_length=50, null=True)
    add_date = models.DateTimeField(auto_now_add=True, null=True)
    edit_date = models.DateTimeField(auto_now=True, null=True)


################################## Piutang Models ##################################

class jenis_transaksi_db(models.Model):
    jenis_transaksi = models.CharField(max_length=100)
    add_by = models.CharField(max_length=100,null=True)
    edit_by = models.CharField(max_length=100,null=True)
    add_date = models.DateTimeField(auto_now_add=True,null=True)
    edit_date = models.DateTimeField(auto_now=True,null=True)
    def __str__(self):
        return self.jenis_transaksi


class jenis_piutang_db(models.Model):
    jenis_transaksi = models.ForeignKey(jenis_transaksi_db,on_delete=models.CASCADE, null=True)
    add_by = models.CharField(max_length=100,null=True)
    edit_by = models.CharField(max_length=100,null=True)
    add_date = models.DateTimeField(auto_now_add=True,null=True)
    edit_date = models.DateTimeField(auto_now=True,null=True)

# class jenis

class piutang_db(models.Model):
    pegawai = models.ForeignKey(pegawai_db,on_delete=models.CASCADE)
    piutang = models.IntegerField()
    pot_piutang = models.IntegerField()
    pemutihan = models.IntegerField()

    add_by = models.CharField(max_length=100,null=True)
    edit_by = models.CharField(max_length=100,null=True)
    add_date = models.DateTimeField(auto_now_add=True,null=True)
    edit_date = models.DateTimeField(auto_now=True,null=True)

class temporary_piutang_db(models.Model):
    tgl = models.DateField(null=True)
    pegawai = models.ForeignKey(pegawai_db,on_delete=models.CASCADE)
    piutang = models.IntegerField()
    pot_piutang = models.IntegerField()
    jenis_piutang = models.ForeignKey(jenis_piutang_db,on_delete=models.CASCADE,null=True)

    add_by = models.CharField(max_length=100,null=True)
    edit_by = models.CharField(max_length=100,null=True)
    add_date = models.DateTimeField(auto_now_add=True,null=True)
    edit_date = models.DateTimeField(auto_now=True,null=True)

class transaksi_db(models.Model):
    tgl = models.DateField()
    pegawai = models.ForeignKey(pegawai_db,on_delete=models.CASCADE)
    nilai = models.IntegerField(null=True)
    nodok = models.CharField(max_length=200,null=True)
    kode_piutang = models.ForeignKey(kode_piutang_db,on_delete=models.CASCADE,null=True)
    jenis_transaksi = models.ForeignKey(jenis_transaksi_db,on_delete=models.CASCADE,null=True)


    add_by = models.CharField(max_length=100,null=True)
    edit_by = models.CharField(max_length=100,null=True)
    add_date = models.DateTimeField(auto_now_add=True,null=True)
    edit_date = models.DateTimeField(auto_now=True,null=True)


class kehilangan_db(models.Model):
    pegawai = models.ForeignKey(pegawai_db,on_delete=models.CASCADE)
    piutang = models.IntegerField()
    pot_piutang = models.IntegerField()
    pemutihan = models.IntegerField()

    add_by = models.CharField(max_length=100,null=True)
    edit_by = models.CharField(max_length=100,null=True)
    add_date = models.DateTimeField(auto_now_add=True,null=True)
    edit_date = models.DateTimeField(auto_now=True,null=True)
    
class ketemu_db(models.Model):
    pegawai = models.ForeignKey(pegawai_db,on_delete=models.CASCADE)
    ketemu = models.IntegerField()
    pemutihan = models.IntegerField(null=True)

    add_by = models.CharField(max_length=100,null=True)
    edit_by = models.CharField(max_length=100,null=True)
    add_date = models.DateTimeField(auto_now_add=True,null=True)
    edit_date = models.DateTimeField(auto_now=True,null=True)



################################## AHRIS Models ##################################
class pegawai_ahris_db(models.Model):
    nama = models.CharField(max_length=200, null=True)
    userid = models.CharField(max_length=100, unique=True, null=True)
    gender = models.CharField(max_length=10, null=True)
    status_id = models.IntegerField(null=False)
    nik = models.CharField(max_length=100, null=True)
    divisi_id = models.IntegerField(null=False)
    counter_id = models.IntegerField(null=False)

    no_rekening = models.CharField(max_length=50, null=True, blank=True)
    no_bpjs_ks = models.CharField(max_length=50, null=True, blank=True)
    no_bpjs_tk = models.CharField(max_length=50, null=True, blank=True)
    payroll_by = models.CharField(max_length=50, choices=pilihan_pengelola, default='HRD')

    ks_premi = models.IntegerField(default=0)
    tk_premi = models.IntegerField(default=0)

    aktif = models.IntegerField(null=True)
    tgl_masuk = models.DateField(null=True, blank=True)
    tgl_aktif = models.DateTimeField(null=True, blank=True)
    tgl_nonaktif = models.DateTimeField(null=True, blank=True)
    sisa_cuti = models.IntegerField(null=True)

    add_by = models.CharField(max_length=100, null=True, blank=True)
    edit_by = models.CharField(max_length=100, null=True, blank=True)
    add_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    edit_date = models.DateTimeField(auto_now=True, null=True)
    def __str__(self) -> str:
        return self.nama
    
    class Meta:
        managed = False
        db_table = "hrd_app_pegawai_db"

class rekap_db(models.Model):
    pegawai = models.ForeignKey(pegawai_ahris_db,on_delete=models.CASCADE)
    tharikerja = models.IntegerField()
    periode = models.IntegerField()
    tahun = models.IntegerField()
    sb = models.IntegerField()
    sdl = models.IntegerField()
    sdp = models.IntegerField()
    ijin = models.IntegerField()
    af = models.IntegerField()
    insentif = models.IntegerField()
    cm = models.IntegerField()
    keterangan = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.pegawai.nama

    class Meta:
        managed=False
        db_table='hrd_app_rekap_db'


class status_ahris_db(models.Model):
    status = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.status

    class Meta:
        managed=False
        db_table='hrd_app_status_pegawai_db'

class status_pegawai_payroll_db(models.Model):
    status_pegawai = models.ForeignKey(status_ahris_db,on_delete=models.CASCADE)

    # def __str__(self) -> int:
    #     return self.status_pegawai_id
    
    class Meta:
        managed=False
        db_table = "hrd_app_status_pegawai_payroll_db"