from ..lib import *

class ApiIjin(APIView):
    def get(self,r,*args, **kwargs):
        print("OKO")
        pass
    def post(self,r,*args, **kwargs):
        data = r.data.get("data")
        data = json.loads(data)
        for dt in data:
            print(dt)
            with transaction.atomic(using=dt["cabang"]):
                try:
                    ijin = data_ijin_db.objects.select_for_update().using(dt["cabang"]).filter(periode=dt["periode"],tahun=dt["tahun"],pegawai_id=int(dt["pegawai_id"]))
                    if not ijin.exists():
                        continue
                    
                    for f in data_ijin_db._meta.get_fields():
                        if dt["col"] == f.name:
                            updObj = {}
                            updObj[dt["col"]] = dt["data"]
                            ijin.update(**updObj)

                except Exception as e:
                    print(e)
                    transaction.set_rollback(True,using=dt["cabang"])
                    continue
        return Response({"sdssd":"ssdd"},status=200)