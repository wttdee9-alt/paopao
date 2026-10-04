from dataclasses import dataclass
from math import isfinite

@dataclass
class SegmentMetrics:
    messages:int=0; orders:int=0; paid_orders:int=0; cod_orders:int=0; refused_cod:int=0
    repeat_orders:int=0; spend:float=0; revenue:float=0; contribution:float=0

@dataclass
class ScoreResult:
    buyer_score:float; confidence:float; smoothed_close_rate:float; reasons:list[str]

def safe_div(a,b): return a/b if b else 0.0
def clamp01(v): return max(0.0,min(1.0,v if isfinite(v) else 0.0))
def bayesian_rate(s,t,p,prior_strength=10.0): return (s+prior_strength*max(0,min(1,p)))/(t+prior_strength)
def confidence_score(messages,orders): return round(.4*min(messages/30,1)+.6*min(orders/10,1),4)
def _ratio(v,b): return clamp01(v/b) if b>0 else (.5 if v>0 else 0)
def _inverse(v,b): return clamp01(b/v) if b>0 and v>0 else 0

def score_segment(s:SegmentMetrics,g:SegmentMetrics,prior_strength=10.0):
    gc=safe_div(g.orders,g.messages); close=bayesian_rate(s.orders,s.messages,gc,prior_strength)
    cpa=safe_div(s.spend,s.orders); gcpa=safe_div(g.spend,g.orders)
    margin=safe_div(s.contribution,s.orders); gmargin=safe_div(g.contribution,g.orders)
    paid=safe_div(s.paid_orders,s.orders); gpaid=safe_div(g.paid_orders,g.orders)
    repeat=safe_div(s.repeat_orders,s.orders); grepeat=safe_div(g.repeat_orders,g.orders)
    refusal=safe_div(s.refused_cod,s.cod_orders); gref=safe_div(g.refused_cod,g.cod_orders)
    cod=.5 if not s.cod_orders else (1 if gref<=0 and refusal==0 else clamp01(1-refusal/max(gref,.01)/2))
    score=100*(.30*_ratio(close,max(gc,.01))+.25*(_inverse(cpa,gcpa) if s.orders else 0)+.20*(_ratio(margin,max(gmargin,1)) if s.orders else 0)+.10*(_ratio(paid,max(gpaid,.01)) if s.orders else 0)+.10*(_ratio(repeat,max(grepeat,.01)) if s.orders else 0)+.05*cod)
    why=[]
    if gc and close>=gc*1.2: why.append(f"อัตราปิดสูงกว่าค่าเฉลี่ย {close/gc:.1f} เท่า")
    if s.orders and gcpa and cpa<=gcpa*.8: why.append(f"ต้นทุนต่อออเดอร์ต่ำกว่าค่าเฉลี่ย {(1-cpa/gcpa)*100:.0f}%")
    if s.cod_orders and refusal<=gref: why.append("COD ตีกลับต่ำกว่าหรือเท่าค่าเฉลี่ย")
    if not why: why.append("ข้อมูลยังไม่มากพอให้ชี้จุดเด่นชัดเจน")
    return ScoreResult(round(clamp01(score/100)*100,1),confidence_score(s.messages,s.orders),round(close,4),why)
