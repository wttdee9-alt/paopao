import json, sqlite3, os
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

def data_dir():
    p=Path(os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or Path.home())/"MetaBuyerIntelligence"; p.mkdir(parents=True,exist_ok=True); return p
SCHEMA="""PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ad_insights(id INTEGER PRIMARY KEY AUTOINCREMENT,date TEXT,hour_bucket TEXT,campaign_id TEXT,adset_id TEXT,ad_id TEXT,age TEXT,gender TEXT,region TEXT,publisher_platform TEXT,platform_position TEXT,device_platform TEXT,spend REAL DEFAULT 0,impressions INTEGER DEFAULT 0,clicks INTEGER DEFAULT 0,messaging_conversations INTEGER DEFAULT 0,purchases INTEGER DEFAULT 0,purchase_value REAL DEFAULT 0,source_grain TEXT,source_key TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,ad_id TEXT,quantity_dozen INTEGER,payment_method TEXT,gross_revenue REAL,shipping_cost REAL,cod_fee REAL,product_cost REAL,packaging_cost REAL,status TEXT,province TEXT,region TEXT,first_order INTEGER,customer_name_enc BLOB,customer_phone_enc BLOB,customer_address_enc BLOB);
CREATE TABLE IF NOT EXISTS recommendations(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,severity TEXT,recommendation_type TEXT,evidence_json TEXT,recommendation_json TEXT,status TEXT DEFAULT 'PENDING',approved_at TEXT);
"""
DEFAULTS={"demo_mode":True,"currency":"THB","target_cost_per_message":30,"target_cpa":150,"spend_cap_warning":300,"meta_api_version":"v24.0","meta_ad_account_id":"","retail_packages":[{"dozen":1,"prepaid_total":180,"cod_total":190},{"dozen":2,"prepaid_total":360,"cod_total":375},{"dozen":3,"prepaid_total":540,"cod_total":560}],"payment_instructions":""}

class Database:
    def __init__(self,path=None):
        self.path=Path(path) if path else data_dir()/"meta_buyer_intelligence.sqlite3"
        with self.connect() as c:c.executescript(SCHEMA)
        for k,v in DEFAULTS.items():
            if self.get_setting(k,None) is None:self.set_setting(k,v)
    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row
        try: yield c; c.commit()
        finally:c.close()
    def set_setting(self,k,v):
        with self.connect() as c:c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",(k,json.dumps(v,ensure_ascii=False)))
    def get_setting(self,k,d=None):
        with self.connect() as c:r=c.execute("SELECT value FROM settings WHERE key=?",(k,)).fetchone()
        return json.loads(r["value"]) if r else d
    def execute(self,sql,p=()):
        with self.connect() as c:c.execute(sql,tuple(p))
    def query(self,sql,p=()):
        with self.connect() as c:return list(c.execute(sql,tuple(p)).fetchall())
    def insert_insight(self,r):
        cols=["date","hour_bucket","campaign_id","adset_id","ad_id","age","gender","region","publisher_platform","platform_position","device_platform","spend","impressions","clicks","messaging_conversations","purchases","purchase_value","source_grain","source_key"]
        with self.connect() as c:c.execute(f"INSERT OR REPLACE INTO ad_insights({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",[r.get(x) for x in cols])
    def add_order(self,r):
        cols=["created_at","ad_id","quantity_dozen","payment_method","gross_revenue","shipping_cost","cod_fee","product_cost","packaging_cost","status","province","region","first_order","customer_name_enc","customer_phone_enc","customer_address_enc"]
        with self.connect() as c:
            cur=c.execute(f"INSERT INTO orders({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",[r.get(x) for x in cols]); return cur.lastrowid
    def list_orders(self):
        return self.query("SELECT * FROM orders ORDER BY created_at DESC")
