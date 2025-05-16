from .lib import *
# Create your views here.


from .payroll.views import *
from .pegawai.views import *
from .piutang.views import *
from .api.ijin import *
from .thr.views import *
from .pengaturan.views import *
# @authorization(["root","it"])
# def status_pegawai_json(r):
    



@authorization(["root","it"])
def setup(r):
    status_payroll = status_pegawai_payroll_db.objects.using(f"p{r.session['ccabang']}").all()
    periode = pperiode(r.session["ccabang"])[0]
    tahun = pperiode(r.session["ccabang"])[1]
    try:
        rekening = rekening_db.objects.using(r.session["ccabang"]).get(bpjs=0)
    except:
        if r.user.is_staff:
            return redirect("rek_sumber_dana")
        messages.error(r,"Rekening non bpjs tidak ada")
        return redirect("login")
    try:
        rek_bpjs = rekening_db.objects.using(r.session["ccabang"]).get(bpjs=1)
    except:
        if r.user.is_staff:
            return redirect("rek_sumber_dana")
        messages.error(r,"Rekening bpjs tidak ada")
        return redirect("login")
    # print(status_payroll
    luserid = []
    for status in status_payroll:
        for p in pegawai_db.objects.using(r.session['ccabang']).filter(status_id=status.status_pegawai.pk):
            if (p.ks_premi == 0 or p.ks_premi == "" or p.ks_premi is None):
                sb_ks = 0
            else:
                sb_ks = 1
            if (p.tk_premi == 0 or p.tk_premi == "" or p.tk_premi is None):
                sb_tk = 0
            else:
                sb_tk = 1
            if p.tk_premi is None or p.tk_premi == 0 or p.tk_premi == "" and p.ks_premi is None or p.ks_premi == 0 or p.ks_premi == "" :
                rek = rek_bpjs.pk
            else:
                rek = rekening.pk
            # print(rek)
            if rekap_db.objects.using(f"p{r.session['ccabang']}").filter(periode=int(periode),tahun=int(tahun),pegawai__userid=int(p.userid)).exists():
                rk = rekap_db.objects.using(f"p{r.session['ccabang']}").get(periode=int(periode),tahun=int(tahun),pegawai__userid=int(p.userid))
                if rk.cm is not None:
                    if rk.cm == 0:
                        if p.no_rekening == "0" or p.no_rekening == "" or p.no_rekening is None:
                            tc = "Cash"
                            status_cm = 0
                        else:
                            tc = "Transfer"
                            status_cm = 0
                    else:
                        if rk.tharikerja > 0:
                            tc = "Transfer_proporsional"
                            status_cm = 1
                        else:
                            tc = "Transfer"
                            status_cm = 1
                else:
                    if p.no_rekening == "0" or p.no_rekening == "" or p.no_rekening is None:
                        tc = "Cash"
                        status_cm = 0
                    else:
                        tc = "Transfer"
                        status_cm = 0
            else:
                if p.no_rekening == "0" or p.no_rekening == "" or p.no_rekening is None:
                    tc = "Cash"
                    status_cm = 0
                else:
                    tc = "Transfer"
                    print(p.nama)
                    print(p.no_rekening)
                    status_cm = 0
            p.t_c = tc
            p.rek_sd_id = rek
            p.save(using=r.session["ccabang"])
            # luserid.append(p.pk)
    return redirect("beranda")



def user_logout(r):
    r.session["ccabang"] = None
    r.session["cabang"] = None
    r.session["user"] = None
    result = os.environ.get("INVALIDATION_URL")
    messages.info(r,"Berhasil logout")
    return redirect(result)
