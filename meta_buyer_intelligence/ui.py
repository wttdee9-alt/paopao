import tkinter as tk
from tkinter import ttk
from .db import Database
from .demo import ensure_demo_data
from .analytics import overview, cod_summary

def money(v):
    return f"฿{float(v):,.2f}"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meta Buyer Intelligence")
        self.geometry("960x600")
        self.db=Database()
        if self.db.get_setting("demo_mode",True):
            ensure_demo_data(self.db)
        self.values={}
        self.build()
        self.refresh()

    def build(self):
        bar=ttk.Frame(self,padding=12)
        bar.pack(fill="x")
        ttk.Label(bar,text="Meta Buyer Intelligence",font=("Segoe UI",18,"bold")).pack(side="left")
        ttk.Button(bar,text="รีเฟรช",command=self.refresh).pack(side="right")

        tabs=ttk.Notebook(self)
        tabs.pack(fill="both",expand=True,padx=12,pady=12)
        overview_tab=ttk.Frame(tabs,padding=12)
        cod_tab=ttk.Frame(tabs,padding=12)
        settings_tab=ttk.Frame(tabs,padding=12)
        tabs.add(overview_tab,text="ภาพรวม")
        tabs.add(cod_tab,text="COD")
        tabs.add(settings_tab,text="ตั้งค่า")

        cards=[
            ("spend","ค่าใช้จ่าย"),
            ("messages","แชต"),
            ("cost_per_message","ต้นทุน/แชต"),
            ("orders","ออเดอร์"),
            ("revenue","รายได้"),
            ("cost_per_order","ต้นทุน/ออเดอร์"),
            ("roas","ROAS"),
            ("contribution_after_ads","เหลือหลังโฆษณา"),
        ]
        for i,(key,label) in enumerate(cards):
            frame=ttk.LabelFrame(overview_tab,text=label,padding=16)
            frame.grid(row=i//4,column=i%4,sticky="nsew",padx=5,pady=5)
            overview_tab.columnconfigure(i%4,weight=1)
            value=ttk.Label(frame,text="-",font=("Segoe UI",14,"bold"))
            value.pack()
            self.values[key]=value

        self.cod_label=ttk.Label(cod_tab,text="",font=("Segoe UI",14,"bold"))
        self.cod_label.pack(anchor="w")

        self.demo=tk.BooleanVar(value=self.db.get_setting("demo_mode",True))
        ttk.Checkbutton(settings_tab,text="Demo Mode",variable=self.demo).pack(anchor="w",pady=8)
        ttk.Button(settings_tab,text="บันทึก",command=self.save).pack(anchor="w")

    def save(self):
        self.db.set_setting("demo_mode",bool(self.demo.get()))

    def refresh(self):
        data=overview(self.db)
        for key,value in data.items():
            if key not in self.values:
                continue
            if key=="roas":
                text=f"{value:.2f}x"
            elif key in ("messages","orders"):
                text=str(int(value))
            else:
                text=money(value)
            self.values[key].config(text=text)

        c=cod_summary(self.db)
        self.cod_label.config(
            text=f'COD {c["total"]} | เก็บสำเร็จ {c["collected"]} | '
                 f'ปฏิเสธ {c["refused"]} | ตีกลับ {c["returned"]} | '
                 f'Refusal {c["refusal_rate"]:.1f}% | Loss {money(c["estimated_loss"])}'
        )

def run_app():
    App().mainloop()
