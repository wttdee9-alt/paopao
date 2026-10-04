import json
from datetime import datetime
from .analytics import overview,segment_scores

def regenerate_recommendations(db):
    ov=overview(db);cpm=float(db.get_setting("target_cost_per_message",30));cpa=float(db.get_setting("target_cpa",150)); rec=[]
    if ov["messages"]==0 and ov["spend"]>cpm*2:rec.append(("ACTION","CHAT_DELIVERY_ISSUE","มีค่าใช้จ่ายแต่ยังไม่มีแชต",ov))
    elif ov["cost_per_message"]>cpm:rec.append(("ACTION","COST_PER_MESSAGE_HIGH","ต้นทุนต่อแชตสูงกว่าเป้า",ov))
    if ov["orders"]==0 and ov["spend"]>cpa:rec.append(("ACTION","SPEND_NO_ORDER","ใช้เงินเกิน Target CPA แต่ยังไม่มีออเดอร์",ov))
    for s in segment_scores(db,"region"):
        if s["buyer_score"]>=75 and s["confidence"]>=.65:rec.append(("ACTION","SCALE_CANDIDATE",f"กลุ่ม {s['segment']} เป็นผู้ชนะที่มีความมั่นใจสูง",s))
    db.execute("DELETE FROM recommendations WHERE status='PENDING'")
    for sev,typ,title,evidence in rec:db.execute("INSERT INTO recommendations(created_at,severity,recommendation_type,evidence_json,recommendation_json,status) VALUES(?,?,?,?,?,?)",(datetime.utcnow().isoformat(),sev,typ,json.dumps(evidence,ensure_ascii=False),json.dumps({"title":title},ensure_ascii=False),"PENDING"))
    return rec
