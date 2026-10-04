import threading
import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk, messagebox

from .db import Database
from .analytics import overview, cod_summary
from .security import get_secret, set_secret
from .meta_provider import MetaAdsProvider, sync_meta_to_db


def money(v):
    return f"฿{float(v):,.2f}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meta Buyer Intelligence")
        self.geometry("1080x680")
        self.minsize(980, 620)
        self.db = Database()
        self.values = {}
        self.account_map = {}
        self.build()
        self.refresh()

    def build(self):
        bar = ttk.Frame(self, padding=12)
        bar.pack(fill="x")
        ttk.Label(
            bar,
            text="Meta Buyer Intelligence",
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")
        self.status_var = tk.StringVar(value="พร้อมใช้งาน")
        ttk.Label(bar, textvariable=self.status_var).pack(side="left", padx=18)
        ttk.Button(bar, text="รีเฟรช", command=self.refresh).pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        overview_tab = ttk.Frame(self.tabs, padding=12)
        cod_tab = ttk.Frame(self.tabs, padding=12)
        settings_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(overview_tab, text="ภาพรวม")
        self.tabs.add(cod_tab, text="COD")
        self.tabs.add(settings_tab, text="เชื่อม Meta")

        cards = [
            ("spend", "ค่าใช้จ่าย"),
            ("messages", "แชต"),
            ("cost_per_message", "ต้นทุน/แชต"),
            ("orders", "ออเดอร์"),
            ("revenue", "รายได้"),
            ("cost_per_order", "ต้นทุน/ออเดอร์"),
            ("roas", "ROAS"),
            ("contribution_after_ads", "เหลือหลังโฆษณา"),
        ]
        for i, (key, label) in enumerate(cards):
            frame = ttk.LabelFrame(overview_tab, text=label, padding=16)
            frame.grid(
                row=i // 4,
                column=i % 4,
                sticky="nsew",
                padx=5,
                pady=5,
            )
            overview_tab.columnconfigure(i % 4, weight=1)
            value = ttk.Label(frame, text="-", font=("Segoe UI", 14, "bold"))
            value.pack()
            self.values[key] = value

        ttk.Label(
            overview_tab,
            text="ตัวเลขโฆษณามาจากข้อมูลที่ Sync จาก Meta Ads API ส่วนยอดขายมาจากออเดอร์จริงในระบบ",
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(24, 4))

        self.cod_label = ttk.Label(
            cod_tab,
            text="",
            font=("Segoe UI", 14, "bold"),
        )
        self.cod_label.pack(anchor="w")

        connect = ttk.LabelFrame(
            settings_tab,
            text="เชื่อมบัญชีโฆษณา Meta",
            padding=14,
        )
        connect.pack(fill="x")

        ttk.Label(connect, text="Access Token").grid(row=0, column=0, sticky="w", pady=5)
        self.token_var = tk.StringVar(value=get_secret("meta_access_token") or "")
        self.token_entry = ttk.Entry(
            connect,
            textvariable=self.token_var,
            width=74,
            show="•",
        )
        self.token_entry.grid(row=0, column=1, columnspan=3, sticky="ew", padx=8, pady=5)

        ttk.Label(connect, text="API Version").grid(row=1, column=0, sticky="w", pady=5)
        self.api_var = tk.StringVar(
            value=str(self.db.get_setting("meta_api_version", "v24.0"))
        )
        ttk.Entry(connect, textvariable=self.api_var, width=18).grid(
            row=1, column=1, sticky="w", padx=8, pady=5
        )

        ttk.Label(connect, text="Ad Account").grid(row=2, column=0, sticky="w", pady=5)
        self.account_var = tk.StringVar()
        self.account_combo = ttk.Combobox(
            connect,
            textvariable=self.account_var,
            width=58,
            state="readonly",
        )
        self.account_combo.grid(row=2, column=1, columnspan=2, sticky="ew", padx=8, pady=5)

        ttk.Button(
            connect,
            text="ตรวจสอบ Token / โหลดบัญชี",
            command=self.load_accounts,
        ).grid(row=1, column=2, padx=8, pady=5)

        ttk.Button(
            connect,
            text="บันทึกการเชื่อมต่อ",
            command=self.save_connection,
        ).grid(row=1, column=3, padx=8, pady=5)

        sync_box = ttk.LabelFrame(
            settings_tab,
            text="Sync ข้อมูลจริง",
            padding=14,
        )
        sync_box.pack(fill="x", pady=(12, 0))

        ttk.Label(sync_box, text="ช่วงย้อนหลัง").grid(row=0, column=0, sticky="w")
        self.days_var = tk.StringVar(value="30")
        ttk.Combobox(
            sync_box,
            textvariable=self.days_var,
            values=["1", "7", "14", "30", "60", "90"],
            width=10,
            state="readonly",
        ).grid(row=0, column=1, padx=8, sticky="w")

        self.sync_button = ttk.Button(
            sync_box,
            text="Sync Meta Ads ตอนนี้",
            command=self.sync_real_data,
        )
        self.sync_button.grid(row=0, column=2, padx=8)

        self.last_sync_var = tk.StringVar(
            value=str(self.db.get_setting("last_meta_sync", "ยังไม่เคย Sync"))
        )
        ttk.Label(sync_box, textvariable=self.last_sync_var).grid(
            row=1,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(10, 0),
        )

        connect.columnconfigure(1, weight=1)

        saved_account = str(self.db.get_setting("meta_ad_account_id", "") or "")
        if saved_account:
            self.account_var.set(saved_account)

    def _provider(self):
        token = self.token_var.get().strip() or (get_secret("meta_access_token") or "")
        if not token:
            raise ValueError("ยังไม่ได้ใส่ Meta Access Token")
        api_version = self.api_var.get().strip() or "v24.0"
        return MetaAdsProvider(token, api_version)

    def load_accounts(self):
        self.status_var.set("กำลังตรวจสอบ Meta...")
        self.update_idletasks()
        try:
            provider = self._provider()
            accounts = provider.list_accounts()
            if not accounts:
                raise RuntimeError("Token นี้ไม่พบบัญชีโฆษณาที่เข้าถึงได้")
            self.account_map = {}
            labels = []
            for account in accounts:
                account_id = str(account.get("account_id") or account.get("id", "")).replace("act_", "")
                name = account.get("name") or account_id
                currency = account.get("currency") or ""
                label = f"{name} | {account_id} | {currency}"
                labels.append(label)
                self.account_map[label] = account_id
            self.account_combo["values"] = labels

            saved = str(self.db.get_setting("meta_ad_account_id", "") or "")
            chosen = None
            for label, account_id in self.account_map.items():
                if account_id == saved:
                    chosen = label
                    break
            self.account_combo.set(chosen or labels[0])
            self.status_var.set(f"เชื่อมต่อได้: {len(accounts)} บัญชี")
            messagebox.showinfo("Meta", "ตรวจสอบ Token สำเร็จ และโหลดบัญชีโฆษณาแล้ว")
        except Exception as exc:
            self.status_var.set("เชื่อมต่อ Meta ไม่สำเร็จ")
            messagebox.showerror("Meta connection error", str(exc))

    def save_connection(self):
        token = self.token_var.get().strip()
        if token:
            set_secret("meta_access_token", token)
        self.db.set_setting("meta_api_version", self.api_var.get().strip() or "v24.0")

        selected = self.account_var.get().strip()
        account_id = self.account_map.get(selected, selected)
        account_id = account_id.replace("act_", "")
        if account_id:
            self.db.set_setting("meta_ad_account_id", account_id)

        self.status_var.set("บันทึกการเชื่อมต่อแล้ว")
        messagebox.showinfo("บันทึก", "บันทึกการเชื่อมต่อ Meta แล้ว")

    def sync_real_data(self):
        if self.sync_button["state"] == "disabled":
            return
        self.save_connection()

        account_id = str(self.db.get_setting("meta_ad_account_id", "") or "").replace("act_", "")
        if not account_id:
            messagebox.showerror("Sync", "กรุณาโหลดและเลือก Ad Account ก่อน")
            return

        try:
            days = max(1, int(self.days_var.get()))
        except ValueError:
            days = 30

        self.sync_button.config(state="disabled")
        self.status_var.set("กำลัง Sync ข้อมูล Meta จริง...")
        threading.Thread(
            target=self._sync_worker,
            args=(account_id, days),
            daemon=True,
        ).start()

    def _sync_worker(self, account_id, days):
        try:
            provider = self._provider()
            until = date.today()
            since = until - timedelta(days=days - 1)
            counts = sync_meta_to_db(
                self.db,
                provider,
                account_id,
                since.isoformat(),
                until.isoformat(),
            )
            total = sum(counts.values())
            stamp = f"Sync สำเร็จ {date.today().isoformat()} | {total} rows | account {account_id}"
            self.db.set_setting("last_meta_sync", stamp)
            self.after(0, lambda: self._sync_done(stamp, counts))
        except Exception as exc:
            self.after(0, lambda: self._sync_failed(str(exc)))

    def _sync_done(self, stamp, counts):
        self.sync_button.config(state="normal")
        self.last_sync_var.set(stamp)
        self.status_var.set("Sync Meta สำเร็จ")
        self.refresh()
        detail = ", ".join(f"{k}={v}" for k, v in counts.items())
        messagebox.showinfo("Sync สำเร็จ", f"ดึงข้อมูลจริงจาก Meta แล้ว\n{detail}")

    def _sync_failed(self, error):
        self.sync_button.config(state="normal")
        self.status_var.set("Sync Meta ไม่สำเร็จ")
        messagebox.showerror("Meta Sync Error", error)

    def refresh(self):
        data = overview(self.db)
        for key, value in data.items():
            if key not in self.values:
                continue
            if key == "roas":
                text = f"{value:.2f}x"
            elif key in ("messages", "orders"):
                text = str(int(value))
            else:
                text = money(value)
            self.values[key].config(text=text)

        c = cod_summary(self.db)
        self.cod_label.config(
            text=(
                f'COD {c["total"]} | เก็บสำเร็จ {c["collected"]} | '
                f'ปฏิเสธ {c["refused"]} | ตีกลับ {c["returned"]} | '
                f'Refusal {c["refusal_rate"]:.1f}% | Loss {money(c["estimated_loss"])}'
            )
        )


def run_app():
    App().mainloop()
