import random,hashlib
from datetime import date,datetime,timedelta

def key(*x): return hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()

def ensure_demo_data(db,days=14):
    if db.query("SELECT COUNT(*) n FROM ad_insights")[0]["n"]: return
    rng=random.Random(42); today=date.today()
    ads=["AD-180-A","AD-180-B","AD-HERITAGE"]
    regions=["กรุงเทพฯ","ภาคกลาง","ภาคเหนือ","ภาคอีสาน","ภาคใต้"]
    for d in range(days):
        day=today-timedelta(days=days-1-d)
        for ad in ads:
            spend=rng.uniform(70,220); msgs=max(0,int(spend/rng.uniform(11,30))); imp=int(spend/rng.uniform(.045,.095)*1000); clicks=max(msgs*4,int(imp*rng.uniform(.035,.09)))
            db.insert_insight({"date":day.isoformat(),"campaign_id":"DEMO","adset_id":"DEMO","ad_id":ad,"spend":spend,"impressions":imp,"clicks":clicks,"messaging_conversations":msgs,"purchases":0,"purchase_value":0,"source_grain":"base","source_key":key(day,ad,"base")})
            for h in range(8,22):
                s=max(0,rng.gauss(spend/14,3)); m=max(0,int(s/rng.uniform(9,35))); i=max(1,int(s/rng.uniform(.05,.11)*1000)); c=max(0,int(i*rng.uniform(.03,.1)))
                db.insert_insight({"date":day.isoformat(),"hour_bucket":f"{h:02d}:00-{h:02d}:59","campaign_id":"DEMO","adset_id":"DEMO","ad_id":ad,"spend":s,"impressions":i,"clicks":c,"messaging_conversations":m,"purchases":0,"purchase_value":0,"source_grain":"hourly","source_key":key(day,ad,h)})
            for reg in regions:
                s=spend*rng.uniform(.12,.28); m=max(0,int(s/rng.uniform(10,35)))
                db.insert_insight({"date":day.isoformat(),"campaign_id":"DEMO","adset_id":"DEMO","ad_id":ad,"region":reg,"spend":s,"impressions":0,"clicks":0,"messaging_conversations":m,"purchases":0,"purchase_value":0,"source_grain":"region","source_key":key(day,ad,reg)})
    for i in range(120):
        dozen=rng.choices([1,2,3],[.65,.25,.1])[0]; pay=rng.choice(["PREPAID","COD","COD"])
        prices={1:(180,190),2:(360,375),3:(540,560)}; rev=prices[dozen][1 if pay=="COD" else 0]
        status=rng.choices(["COD_COLLECTED","PAID","DELIVERED","REFUSED","RETURNED"],[28,25,25,5,2])[0] if pay=="COD" else rng.choice(["PAID","DELIVERED"])
        reg=rng.choices(regions,[3,2,2,2,4])[0]
        db.add_order({"created_at":datetime.combine(today-timedelta(days=rng.randint(0,days-1)),datetime.min.time()).replace(hour=rng.randint(9,20)).isoformat(),"ad_id":rng.choice(ads),"quantity_dozen":dozen,"payment_method":pay,"gross_revenue":rev,"shipping_cost":45+dozen*8,"cod_fee":rev*.025 if pay=="COD" else 0,"product_cost":dozen*12*6.5,"packaging_cost":8+dozen*3,"status":status,"province":reg,"region":reg,"first_order":0 if rng.random()<.12 else 1,"customer_name_enc":None,"customer_phone_enc":None,"customer_address_enc":None})
