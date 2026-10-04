from collections import defaultdict
from datetime import date
from .scoring import SegmentMetrics,score_segment,safe_div

def overview(db,day=None):
    day=day or date.today().isoformat()
    a=db.query("SELECT COALESCE(SUM(spend),0) spend,COALESCE(SUM(impressions),0) impressions,COALESCE(SUM(clicks),0) clicks,COALESCE(SUM(messaging_conversations),0) messages FROM ad_insights WHERE date=? AND source_grain='base'",(day,))[0]
    o=db.query("SELECT COUNT(*) orders,COALESCE(SUM(gross_revenue),0) revenue,COALESCE(SUM(product_cost+shipping_cost+cod_fee+packaging_cost),0) costs FROM orders WHERE substr(created_at,1,10)=? AND status IN ('CONFIRMED','PAID','SHIPPED','DELIVERED','COD_COLLECTED')",(day,))[0]
    spend=float(a["spend"]); msgs=int(a["messages"]); orders=int(o["orders"]); rev=float(o["revenue"]); costs=float(o["costs"])
    return {"spend":spend,"impressions":a["impressions"],"clicks":a["clicks"],"messages":msgs,"orders":orders,"revenue":rev,"cost_per_message":safe_div(spend,msgs),"cost_per_order":safe_div(spend,orders),"roas":safe_div(rev,spend),"contribution_after_ads":rev-costs-spend}

def hourly_rows(db,day=None):
    day=day or date.today().isoformat()
    return [dict(r) for r in db.query("SELECT hour_bucket,SUM(spend) spend,SUM(impressions) impressions,SUM(clicks) clicks,SUM(messaging_conversations) messages FROM ad_insights WHERE date=? AND source_grain='hourly' GROUP BY hour_bucket ORDER BY hour_bucket",(day,))]

def segment_scores(db,dimension="region"):
    insight_grain={"region":"region","ad_id":"base"}.get(dimension)
    ins={}
    if insight_grain:
        for r in db.query(f"SELECT COALESCE({dimension},'ไม่ระบุ') segment,SUM(spend) spend,SUM(messaging_conversations) messages FROM ad_insights WHERE source_grain=? GROUP BY COALESCE({dimension},'ไม่ระบุ')",(insight_grain,)):
            ins[r["segment"]]=SegmentMetrics(messages=int(r["messages"] or 0),spend=float(r["spend"] or 0))
    orders=defaultdict(SegmentMetrics)
    for r in db.list_orders():
        k=str(r[dimension] if dimension in r.keys() and r[dimension] else "ไม่ระบุ"); m=orders[k]
        if r["status"] in ("CONFIRMED","PAID","SHIPPED","DELIVERED","COD_COLLECTED"):
            m.orders+=1;m.revenue+=float(r["gross_revenue"] or 0);m.contribution+=float(r["gross_revenue"] or 0)-float(r["product_cost"] or 0)-float(r["shipping_cost"] or 0)-float(r["cod_fee"] or 0)-float(r["packaging_cost"] or 0)
        if r["status"] in ("PAID","DELIVERED","COD_COLLECTED"):m.paid_orders+=1
        if r["payment_method"]=="COD":
            m.cod_orders+=1
            if r["status"]=="REFUSED":m.refused_cod+=1
        if r["first_order"]==0:m.repeat_orders+=1
    merged={};g=SegmentMetrics()
    for k in set(ins)|set(orders):
        a=ins.get(k,SegmentMetrics());b=orders.get(k,SegmentMetrics());m=SegmentMetrics(a.messages,b.orders,b.paid_orders,b.cod_orders,b.refused_cod,b.repeat_orders,a.spend,b.revenue,b.contribution);merged[k]=m
        for f in vars(g):setattr(g,f,getattr(g,f)+getattr(m,f))
    out=[]
    for k,m in merged.items():
        s=score_segment(m,g);out.append({"segment":k,"spend":m.spend,"messages":m.messages,"orders":m.orders,"close_rate":safe_div(m.orders,m.messages)*100,"cpa":safe_div(m.spend,m.orders),"revenue":m.revenue,"buyer_score":s.buyer_score,"confidence":s.confidence,"reasons":" | ".join(s.reasons)})
    return sorted(out,key=lambda x:(x["buyer_score"],x["confidence"]),reverse=True)

def cod_summary(db):
    r=db.query("SELECT COUNT(*) total,SUM(CASE WHEN status='COD_COLLECTED' THEN 1 ELSE 0 END) collected,SUM(CASE WHEN status='REFUSED' THEN 1 ELSE 0 END) refused,SUM(CASE WHEN status='RETURNED' THEN 1 ELSE 0 END) returned,COALESCE(SUM(CASE WHEN status IN ('REFUSED','RETURNED') THEN shipping_cost+packaging_cost ELSE 0 END),0) loss FROM orders WHERE payment_method='COD'")[0]
    total=int(r["total"] or 0); refused=int(r["refused"] or 0)
    return {"total":total,"collected":int(r["collected"] or 0),"refused":refused,"returned":int(r["returned"] or 0),"refusal_rate":safe_div(refused,total)*100,"estimated_loss":float(r["loss"] or 0)}
