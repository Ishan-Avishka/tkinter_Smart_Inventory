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

    def _export_sales(self):
        conn = get_connection()
        rows = conn.execute("""SELECT invoice_number, customer_name, customer_email,
            customer_phone, sale_date, total_amount, discount, tax, payment_method,
            status, notes FROM sales_records ORDER BY sale_date DESC""").fetchall()
        conn.close()
        self._save_csv(
            f"sales_records_{datetime.now().strftime('%Y%m%d')}.csv",
            ["Invoice","Customer","Email","Phone","Date","Total","Discount",
             "Tax","Payment","Status","Notes"],
            [tuple(r) for r in rows])

    def _export_movements(self):
        conn = get_connection()
        rows = conn.execute("""SELECT sm.moved_at, p.sku, p.name,
            sm.movement_type, sm.quantity, sm.stock_before, sm.stock_after,
            sm.reference_type, sm.notes, sm.moved_by
            FROM stock_movements sm JOIN products p ON p.id=sm.product_id
            ORDER BY sm.moved_at DESC""").fetchall()
        conn.close()
        self._save_csv(
            f"stock_movements_{datetime.now().strftime('%Y%m%d')}.csv",
            ["Date","SKU","Product","Type","Quantity","Stock Before","Stock After",
             "Reference","Notes","By"],
            [tuple(r) for r in rows])

    def _export_alerts(self):
        conn = get_connection()
        rows = conn.execute("""SELECT a.alert_type, p.name, p.sku, a.message,
            a.created_at, CASE a.is_read WHEN 1 THEN 'Read' ELSE 'Unread' END AS status
            FROM alerts a LEFT JOIN products p ON p.id=a.product_id
            ORDER BY a.created_at DESC""").fetchall()
        conn.close()
        self._save_csv(
            f"alerts_{datetime.now().strftime('%Y%m%d')}.csv",
            ["Type","Product","SKU","Message","Created At","Status"],
            [tuple(r) for r in rows])

    # ── PDF ────────────────────────────────────────────────────────────────
    def _build_pdf_tab(self):
        f = self.tab_pdf
        section_header(f, "PDF Report Generator").pack(fill="x", padx=12, pady=(12, 4))

        opt_f = tk.Frame(f, bg=COLORS["bg_card"])
        opt_f.pack(fill="x", padx=12, pady=8)

        tk.Label(opt_f, text="Report Type:", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=0, column=0, sticky="w", padx=12, pady=8)
        self.v_pdf_type = tk.StringVar(value="Inventory Summary")
        ttk.Combobox(opt_f, textvariable=self.v_pdf_type,
                     values=["Inventory Summary", "Stock Status Report",
                              "Sales Report", "Purchase Orders Report",
                              "Low Stock Report", "Full Warehouse Report"],
                     state="readonly", width=28, font=FONTS["entry"]).grid(
            row=0, column=1, sticky="ew", padx=12, pady=8)

        tk.Label(opt_f, text="Company Name:", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=1, column=0, sticky="w", padx=12, pady=8)
        self.v_company = tk.StringVar(value="Smart Inventory Co.")
        ttk.Entry(opt_f, textvariable=self.v_company, width=30, font=FONTS["entry"]).grid(
            row=1, column=1, sticky="ew", padx=12, pady=8)

        tk.Label(opt_f, text="Report Title:", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=2, column=0, sticky="w", padx=12, pady=8)
        self.v_title = tk.StringVar(value="Warehouse Management Report")
        ttk.Entry(opt_f, textvariable=self.v_title, width=30, font=FONTS["entry"]).grid(
            row=2, column=1, sticky="ew", padx=12, pady=8)

        btn_row = tk.Frame(f, bg=COLORS["bg_panel"])
        btn_row.pack(fill="x", padx=12, pady=8)
        ttk.Button(btn_row, text="📄 Generate PDF Report",
                   style="Accent.TButton", command=self._gen_pdf).pack(side="left", padx=8)

        # Preview area
        section_header(f, "PDF Preview").pack(fill="x", padx=12, pady=(12, 4))
        self.preview_txt = tk.Text(f, height=12, bg=COLORS["bg_input"],
                                   fg=COLORS["text_secondary"], font=FONTS["mono"],
                                   relief="flat", state="disabled", padx=8, pady=6)
        self.preview_txt.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _gen_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors as rl_colors
            from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                             Paragraph, Spacer)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm

            path = filedialog.asksaveasfilename(
                initialdir=REPORTS_DIR,
                initialfile=f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")])
            if not path: return

            doc = SimpleDocTemplate(path, pagesize=A4,
                                    rightMargin=1.5*cm, leftMargin=1.5*cm,
                                    topMargin=2*cm, bottomMargin=1.5*cm)
            styles = getSampleStyleSheet()
            h1 = ParagraphStyle("h1", fontSize=18, textColor=rl_colors.HexColor("#F97316"),
                                 spaceAfter=8, fontName="Helvetica-Bold")
            h2 = ParagraphStyle("h2", fontSize=13, textColor=rl_colors.HexColor("#3B82F6"),
                                 spaceAfter=6, fontName="Helvetica-Bold")
            body_s = ParagraphStyle("body", fontSize=9, textColor=rl_colors.black,
                                    spaceAfter=4)

            story = []
            story.append(Paragraph(self.v_company.get(), h1))
            story.append(Paragraph(self.v_title.get(), h2))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_s))
            story.append(Spacer(1, 0.5*cm))

            conn = get_connection()
            rtype = self.v_pdf_type.get()

            if rtype in ("Inventory Summary", "Full Warehouse Report",
                         "Stock Status Report", "Low Stock Report"):
                story.append(Paragraph("Product Inventory", h2))
                sql = """SELECT p.sku, p.name, p.current_stock, p.min_stock,
                    p.selling_price, p.status FROM products p WHERE p.status='Active'"""
                if rtype == "Low Stock Report":
                    sql += " AND p.current_stock <= p.min_stock"
                sql += " ORDER BY p.name"
                rows = conn.execute(sql).fetchall()
                tdata = [["SKU", "Product Name", "Stock", "Min", "Price", "Status"]]
                for r in rows:
                    tdata.append([r[0], r[1][:30], str(r[2]), str(r[3]),
                                  f"${r[4]:.2f}", r[5]])
                t = Table(tdata, repeatRows=1, colWidths=[2.5*cm, 7*cm, 2*cm, 2*cm, 2*cm, 2*cm])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), rl_colors.HexColor("#F97316")),
                    ("TEXTCOLOR",  (0,0), (-1,0), rl_colors.white),
                    ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",   (0,0), (-1,-1), 8),
                    ("ROWBACKGROUNDS", (0,1), (-1,-1),
                     [rl_colors.HexColor("#F5F5F5"), rl_colors.white]),
                    ("GRID", (0,0), (-1,-1), 0.3, rl_colors.lightgrey),
                    ("ALIGN", (2,0), (4,-1), "CENTER"),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.5*cm))

            if rtype in ("Sales Report", "Full Warehouse Report"):
                story.append(Paragraph("Recent Sales Records", h2))
                rows = conn.execute("""SELECT invoice_number, customer_name,
                    sale_date, total_amount, payment_method, status
                    FROM sales_records ORDER BY sale_date DESC LIMIT 50""").fetchall()
                tdata = [["Invoice", "Customer", "Date", "Total", "Payment", "Status"]]
                for r in rows:
                    tdata.append([r[0], (r[1] or "Walk-in")[:20],
                                  r[2][:10], f"${r[3]:.2f}", r[4], r[5]])
                t = Table(tdata, repeatRows=1,
                          colWidths=[3.5*cm, 5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), rl_colors.HexColor("#3B82F6")),
                    ("TEXTCOLOR",  (0,0), (-1,0), rl_colors.white),
                    ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",   (0,0), (-1,-1), 8),
                    ("ROWBACKGROUNDS", (0,1), (-1,-1),
                     [rl_colors.HexColor("#F5F5F5"), rl_colors.white]),
                    ("GRID", (0,0), (-1,-1), 0.3, rl_colors.lightgrey),
                ]))
                story.append(t)

            conn.close()
            doc.build(story)
            self.preview_txt.config(state="normal")
            self.preview_txt.delete("1.0", "end")
            self.preview_txt.insert("end",
                f"✓ PDF generated successfully!\n"
                f"Path: {path}\n"
                f"Type: {rtype}\n"
                f"Company: {self.v_company.get()}\n"
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.preview_txt.config(state="disabled")
            info_dialog(self, "PDF Created", f"Report saved:\n{path}")

        except ImportError:
            error_dialog(self, "Missing Package",
                         "reportlab is required for PDF export.\n"
                         "Run: pip install reportlab")
        except Exception as e:
            error_dialog(self, "Export Error", str(e))
