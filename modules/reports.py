"""
modules/reports.py - Export Reports (CSV / PDF)
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os, csv
from datetime import datetime
from core.database import get_connection
from core.theme import COLORS, FONTS
from core.helpers import section_header, info_dialog, error_dialog

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")


class ReportsModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        os.makedirs(REPORTS_DIR, exist_ok=True)
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="EXPORT REPORTS", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(anchor="w", padx=16, pady=(12, 8))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=4)
        self.tab_csv = ttk.Frame(nb, style="Panel.TFrame")
        self.tab_pdf = ttk.Frame(nb, style="Panel.TFrame")
        nb.add(self.tab_csv, text="  CSV Export  ")
        nb.add(self.tab_pdf, text="  PDF Report  ")
        self._build_csv_tab()
        self._build_pdf_tab()

    # ── CSV ────────────────────────────────────────────────────────────────
    def _build_csv_tab(self):
        f = self.tab_csv
        section_header(f, "Select Report to Export").pack(fill="x", padx=12, pady=(12, 4))

        reports = [
            ("📦 Product Inventory",      self._export_products),
            ("📊 Stock Levels",            self._export_stock),
            ("🚚 Supplier List",           self._export_suppliers),
            ("🛒 Purchase Orders",         self._export_pos),
            ("💰 Sales Records",           self._export_sales),
            ("📋 Stock Movement History",  self._export_movements),
            ("🔔 Alerts Log",              self._export_alerts),
        ]

        grid = tk.Frame(f, bg=COLORS["bg_panel"])
        grid.pack(fill="x", padx=12, pady=8)
        for i, (label, cmd) in enumerate(reports):
            card = tk.Frame(grid, bg=COLORS["bg_card"],
                            highlightbackground=COLORS["border"],
                            highlightthickness=1)
            card.grid(row=i // 2, column=i % 2, padx=8, pady=6, sticky="ew")
            grid.columnconfigure(0, weight=1); grid.columnconfigure(1, weight=1)
            tk.Label(card, text=label, bg=COLORS["bg_card"],
                     fg=COLORS["text_primary"], font=FONTS["subtitle"]).pack(
                side="left", padx=12, pady=10)
            ttk.Button(card, text="Export CSV", style="Accent.TButton",
                       command=cmd).pack(side="right", padx=12, pady=10)

        # Log box
        section_header(f, "Export Log").pack(fill="x", padx=12, pady=(12, 4))
        self.log_txt = tk.Text(f, height=6, bg=COLORS["bg_input"],
                               fg=COLORS["text_secondary"], font=FONTS["mono"],
                               relief="flat", state="disabled", padx=8, pady=6)
        self.log_txt.pack(fill="x", padx=12, pady=(0, 12))

    def _log(self, msg):
        self.log_txt.config(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_txt.insert("end", f"[{ts}] {msg}\n")
        self.log_txt.see("end")
        self.log_txt.config(state="disabled")

    def _save_csv(self, filename, headers, rows):
        path = filedialog.asksaveasfilename(
            initialdir=REPORTS_DIR,
            initialfile=filename,
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if not path: return None
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        self._log(f"Saved: {path}")
        info_dialog(self, "Export Complete", f"Report saved:\n{path}")
        return path

    def _export_products(self):
        conn = get_connection()
        rows = conn.execute("""SELECT p.sku, p.name, c.name AS category,
            s.name AS supplier, p.unit, p.cost_price, p.selling_price,
            p.current_stock, p.min_stock, p.max_stock, p.reorder_point,
            p.barcode, p.location, p.status, p.created_at
            FROM products p
            LEFT JOIN categories c ON c.id=p.category_id
            LEFT JOIN suppliers s ON s.id=p.supplier_id
            ORDER BY p.name""").fetchall()
        conn.close()
        self._save_csv(
            f"products_{datetime.now().strftime('%Y%m%d')}.csv",
            ["SKU","Name","Category","Supplier","Unit","Cost Price","Selling Price",
             "Current Stock","Min Stock","Max Stock","Reorder Point","Barcode",
             "Location","Status","Created At"],
            [tuple(r) for r in rows])

    def _export_stock(self):
        conn = get_connection()
        rows = conn.execute("""SELECT p.sku, p.name, p.current_stock, p.min_stock,
            p.max_stock, p.reorder_point,
            CASE WHEN p.current_stock=0 THEN 'Out of Stock'
                 WHEN p.current_stock<=p.min_stock THEN 'Low Stock'
                 WHEN p.current_stock>=p.max_stock THEN 'Overstocked'
                 ELSE 'OK' END AS stock_status,
            p.location, c.name AS category
            FROM products p LEFT JOIN categories c ON c.id=p.category_id
            WHERE p.status='Active' ORDER BY p.current_stock ASC""").fetchall()
        conn.close()
        self._save_csv(
            f"stock_levels_{datetime.now().strftime('%Y%m%d')}.csv",
            ["SKU","Name","Current Stock","Min Stock","Max Stock",
             "Reorder Point","Status","Location","Category"],
            [tuple(r) for r in rows])

    def _export_suppliers(self):
        conn = get_connection()
        rows = conn.execute("SELECT name,contact_person,email,phone,address,city,country,payment_terms,status FROM suppliers ORDER BY name").fetchall()
        conn.close()
        self._save_csv(
            f"suppliers_{datetime.now().strftime('%Y%m%d')}.csv",
            ["Name","Contact","Email","Phone","Address","City","Country","Payment Terms","Status"],
            [tuple(r) for r in rows])

    def _export_pos(self):
        conn = get_connection()
        rows = conn.execute("""SELECT po.po_number, s.name AS supplier, po.order_date,
            po.expected_date, po.received_date, po.total_amount, po.status, po.notes
            FROM purchase_orders po LEFT JOIN suppliers s ON s.id=po.supplier_id
            ORDER BY po.order_date DESC""").fetchall()
        conn.close()
        self._save_csv(
            f"purchase_orders_{datetime.now().strftime('%Y%m%d')}.csv",
            ["PO Number","Supplier","Order Date","Expected Date","Received Date",
             "Total Amount","Status","Notes"],
            [tuple(r) for r in rows])