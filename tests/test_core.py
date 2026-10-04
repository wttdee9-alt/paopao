from pathlib import Path
from meta_buyer_intelligence.scoring import SegmentMetrics,score_segment,confidence_score
from meta_buyer_intelligence.db import Database
from meta_buyer_intelligence.analytics import cod_summary

def test_score():
    g=SegmentMetrics(messages=100,orders=10,paid_orders=9,cod_orders=5,refused_cod=1,spend=1000,revenue=2000,contribution=900)
    w=SegmentMetrics(messages=30,orders=8,paid_orders=8,cod_orders=3,refused_cod=0,spend=300,revenue=1500,contribution=800)
    assert score_segment(w,g).buyer_score>50
    assert confidence_score(30,10)==1.0

def test_db(tmp_path:Path):
    db=Database(tmp_path/"t.db")
    db.add_order({"created_at":"2026-10-04T10:00:00","ad_id":"A","quantity_dozen":1,"payment_method":"COD","gross_revenue":190,"shipping_cost":50,"cod_fee":5,"product_cost":70,"packaging_cost":10,"status":"REFUSED","province":"BKK","region":"BKK","first_order":1,"customer_name_enc":None,"customer_phone_enc":None,"customer_address_enc":None})
    c=cod_summary(db)
    assert c["total"]==1 and c["refused"]==1
