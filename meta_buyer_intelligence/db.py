import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


def data_dir():
    p = Path(os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or Path.home()) / "MetaBuyerIntelligence"
    p.mkdir(parents=True, exist_ok=True)
    return p


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS settings(
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clients(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    external_account_id TEXT,
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL,
    last_sync TEXT,
    UNIQUE(external_account_id, source)
);

CREATE TABLE IF NOT EXISTS client_account_state(
    client_id INTEGER PRIMARY KEY,
    account_status TEXT,
    account_balance REAL DEFAULT 0,
    amount_spent REAL DEFAULT 0,
    spend_cap REAL DEFAULT 0,
    captured_at TEXT,
    FOREIGN KEY(client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS ad_insights(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    date TEXT,
    hour_bucket TEXT,
    campaign_id TEXT,
    campaign_name TEXT,
    adset_id TEXT,
    adset_name TEXT,
    ad_id TEXT,
    ad_name TEXT,
    age TEXT,
    gender TEXT,
    region TEXT,
    publisher_platform TEXT,
    platform_position TEXT,
    device_platform TEXT,
    spend REAL DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    ctr REAL DEFAULT 0,
    cpc REAL DEFAULT 0,
    cpm REAL DEFAULT 0,
    messaging_conversations INTEGER DEFAULT 0,
    purchases INTEGER DEFAULT 0,
    purchase_value REAL DEFAULT 0,
    effective_status TEXT,
    campaign_daily_budget REAL DEFAULT 0,
    source_grain TEXT,
    source_key TEXT UNIQUE,
    FOREIGN KEY(client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    created_at TEXT,
    ad_id TEXT,
    quantity_dozen INTEGER,
    payment_method TEXT,
    gross_revenue REAL,
    shipping_cost REAL,
    cod_fee REAL,
    product_cost REAL,
    packaging_cost REAL,
    status TEXT,
    province TEXT,
    region TEXT,
    first_order INTEGER,
    customer_name_enc BLOB,
    customer_phone_enc BLOB,
    customer_address_enc BLOB,
    FOREIGN KEY(client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS recommendations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    created_at TEXT,
    severity TEXT,
    recommendation_type TEXT,
    evidence_json TEXT,
    recommendation_json TEXT,
    status TEXT DEFAULT 'PENDING',
    approved_at TEXT,
    FOREIGN KEY(client_id) REFERENCES clients(id)
);
"""


DEFAULTS = {
    "demo_mode": False,
    "currency": "THB",
    "target_cost_per_message": 30,
    "target_cpa": 150,
    "spend_cap_warning": 300,
    "meta_api_version": "v24.0",
    "meta_ad_account_id": "",
    "active_client_id": None,
    "retail_packages": [
        {"dozen": 1, "prepaid_total": 180, "cod_total": 190},
        {"dozen": 2, "prepaid_total": 360, "cod_total": 375},
        {"dozen": 3, "prepaid_total": 540, "cod_total": 560},
    ],
    "payment_instructions": "",
}


class Database:
    def __init__(self, path=None):
        self.path = Path(path) if path else data_dir() / "meta_buyer_intelligence.sqlite3"
        with self.connect() as c:
            c.executescript(SCHEMA)
        self._migrate()
        for k, v in DEFAULTS.items():
            if self.get_setting(k, None) is None:
                self.set_setting(k, v)

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        finally:
            c.close()

    def _columns(self, table):
        with self.connect() as c:
            return {r["name"] for r in c.execute(f"PRAGMA table_info({table})")}

    def _ensure_column(self, table, name, declaration):
        if name not in self._columns(table):
            with self.connect() as c:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")

    def _migrate(self):
        insight_columns = {
            "client_id": "INTEGER",
            "campaign_name": "TEXT",
            "adset_name": "TEXT",
            "ad_name": "TEXT",
            "ctr": "REAL DEFAULT 0",
            "cpc": "REAL DEFAULT 0",
            "cpm": "REAL DEFAULT 0",
            "effective_status": "TEXT",
            "campaign_daily_budget": "REAL DEFAULT 0",
        }
        for name, declaration in insight_columns.items():
            self._ensure_column("ad_insights", name, declaration)
        self._ensure_column("orders", "client_id", "INTEGER")
        self._ensure_column("recommendations", "client_id", "INTEGER")

    def set_setting(self, key, value):
        with self.connect() as c:
            c.execute(
                "INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",
                (key, json.dumps(value, ensure_ascii=False)),
            )

    def get_setting(self, key, default=None):
        with self.connect() as c:
            row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    def execute(self, sql, params=()):
        with self.connect() as c:
            c.execute(sql, tuple(params))

    def query(self, sql, params=()):
        with self.connect() as c:
            return list(c.execute(sql, tuple(params)).fetchall())

    def upsert_client(self, name, external_account_id="", source="manual", last_sync=None):
        external_account_id = str(external_account_id or "").strip()
        with self.connect() as c:
            row = None
            if external_account_id:
                row = c.execute(
                    "SELECT id FROM clients WHERE external_account_id=? AND source=?",
                    (external_account_id, source),
                ).fetchone()
            if row:
                client_id = int(row["id"])
                c.execute(
                    "UPDATE clients SET name=?, last_sync=COALESCE(?,last_sync) WHERE id=?",
                    (name, last_sync, client_id),
                )
            else:
                cur = c.execute(
                    "INSERT INTO clients(name,external_account_id,source,created_at,last_sync) VALUES(?,?,?,?,?)",
                    (
                        name,
                        external_account_id or None,
                        source,
                        datetime.now().isoformat(timespec="seconds"),
                        last_sync,
                    ),
                )
                client_id = int(cur.lastrowid)
        return client_id

    def list_clients(self):
        return self.query("SELECT * FROM clients ORDER BY name")

    def set_active_client(self, client_id):
        self.set_setting("active_client_id", int(client_id) if client_id else None)

    def active_client_id(self):
        value = self.get_setting("active_client_id", None)
        return int(value) if value else None

    def active_client(self):
        client_id = self.active_client_id()
        if not client_id:
            return None
        rows = self.query("SELECT * FROM clients WHERE id=?", (client_id,))
        return dict(rows[0]) if rows else None

    def upsert_account_state(self, client_id, state):
        with self.connect() as c:
            c.execute(
                """
                INSERT OR REPLACE INTO client_account_state(
                    client_id,account_status,account_balance,amount_spent,spend_cap,captured_at
                ) VALUES(?,?,?,?,?,?)
                """,
                (
                    client_id,
                    state.get("account_status"),
                    float(state.get("account_balance") or 0),
                    float(state.get("amount_spent") or 0),
                    float(state.get("spend_cap") or 0),
                    state.get("captured_at"),
                ),
            )

    def get_account_state(self, client_id=None):
        client_id = client_id or self.active_client_id()
        if not client_id:
            return None
        rows = self.query("SELECT * FROM client_account_state WHERE client_id=?", (client_id,))
        return dict(rows[0]) if rows else None

    def insert_insight(self, row):
        cols = [
            "client_id","date","hour_bucket","campaign_id","campaign_name","adset_id","adset_name",
            "ad_id","ad_name","age","gender","region","publisher_platform","platform_position",
            "device_platform","spend","impressions","clicks","ctr","cpc","cpm",
            "messaging_conversations","purchases","purchase_value","effective_status",
            "campaign_daily_budget","source_grain","source_key"
        ]
        if row.get("client_id") is None:
            row["client_id"] = self.active_client_id()
        with self.connect() as c:
            c.execute(
                f"INSERT OR REPLACE INTO ad_insights({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",
                [row.get(x) for x in cols],
            )

    def add_order(self, row):
        cols = [
            "client_id","created_at","ad_id","quantity_dozen","payment_method","gross_revenue",
            "shipping_cost","cod_fee","product_cost","packaging_cost","status","province","region",
            "first_order","customer_name_enc","customer_phone_enc","customer_address_enc"
        ]
        if row.get("client_id") is None:
            row["client_id"] = self.active_client_id()
        with self.connect() as c:
            cur = c.execute(
                f"INSERT INTO orders({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",
                [row.get(x) for x in cols],
            )
            return cur.lastrowid

    def list_orders(self, client_id=None):
        client_id = client_id or self.active_client_id()
        if client_id:
            return self.query(
                "SELECT * FROM orders WHERE client_id=? ORDER BY created_at DESC",
                (client_id,),
            )
        return self.query("SELECT * FROM orders ORDER BY created_at DESC")
