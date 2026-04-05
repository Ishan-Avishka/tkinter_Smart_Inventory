"""
main.py - Smart Inventory & Warehouse Management System
Main Application Entry Point
"""

import tkinter as tk
from tkinter import ttk
import sys, os

# Ensure modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from core.database import initialize_database
from core.theme import COLORS, FONTS, apply_theme
from modules.alerts import check_and_create_alerts, unread_alert_count


# ── Sidebar Navigation Item ───────────────────────────────────────────────
class NavItem(tk.Frame):
    def __init__(self, parent, icon, label, command, is_active=False):
        super().__init__(parent, bg=COLORS["bg_panel"], cursor="hand2")
        self.command = command
        self.is_active = is_active
        self.icon = icon
        self.label_text = label

        self._indicator = tk.Frame(self, bg=COLORS["bg_panel"], width=4)
        self._indicator.pack(side="left", fill="y")

        inner = tk.Frame(self, bg=COLORS["bg_panel"])
        inner.pack(side="left", fill="both", expand=True, padx=8, pady=6)

        self.lbl_icon = tk.Label(inner, text=icon, bg=COLORS["bg_panel"],
                                 fg=COLORS["text_secondary"],
                                 font=("Segoe UI Emoji", 14))
        self.lbl_icon.pack(side="left", padx=(4, 8))

        self.lbl_text = tk.Label(inner, text=label, bg=COLORS["bg_panel"],
                                 fg=COLORS["text_secondary"], font=FONTS["nav"])
        self.lbl_text.pack(side="left")

        self.badge_lbl = None

        self.bind("<Button-1>", lambda _: self.command())
        for w in [inner, self.lbl_icon, self.lbl_text, self._indicator]:
            w.bind("<Button-1>", lambda _: self.command())
        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)
        for w in [inner, self.lbl_icon, self.lbl_text]:
            w.bind("<Enter>", self._on_hover)
            w.bind("<Leave>", self._on_leave)

        if is_active:
            self.set_active(True)

    def _on_hover(self, _=None):
        if not self.is_active:
            for w in [self, self._indicator]:
                w.config(bg=COLORS["bg_hover"])
            self.lbl_icon.config(bg=COLORS["bg_hover"])
            self.lbl_text.config(bg=COLORS["bg_hover"])

    def _on_leave(self, _=None):
        if not self.is_active:
            for w in [self, self._indicator]:
                w.config(bg=COLORS["bg_panel"])
            self.lbl_icon.config(bg=COLORS["bg_panel"])
            self.lbl_text.config(bg=COLORS["bg_panel"])

    def set_active(self, state: bool):
        self.is_active = state
        if state:
            self._indicator.config(bg=COLORS["accent"])
            self.lbl_text.config(fg=COLORS["accent"])
            self.lbl_icon.config(fg=COLORS["accent"])
            self.config(bg=COLORS["bg_card"])
            self._indicator.config(bg=COLORS["accent"])
        else:
            self._indicator.config(bg=COLORS["bg_panel"])
            self.lbl_text.config(fg=COLORS["text_secondary"],
                                 bg=COLORS["bg_panel"])
            self.lbl_icon.config(fg=COLORS["text_secondary"],
                                 bg=COLORS["bg_panel"])
            self.config(bg=COLORS["bg_panel"])

    def set_badge(self, count: int):
        if count > 0:
            text = str(count) if count < 100 else "99+"
            if self.badge_lbl:
                self.badge_lbl.config(text=f" {text} ")
            else:
                self.badge_lbl = tk.Label(self, text=f" {text} ",
                                          bg=COLORS["red"], fg="white",
                                          font=FONTS["badge"])
                self.badge_lbl.pack(side="right", padx=8)
        else:
            if self.badge_lbl:
                self.badge_lbl.destroy()
                self.badge_lbl = None


# ── Main Application ──────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Inventory & Warehouse Management System")
        self.geometry("1440x860")
        self.minsize(1100, 700)
        self.configure(bg=COLORS["bg_dark"])
        self.iconbitmap(default=None)
        apply_theme(self)
        self._build_layout()
        self._modules: dict = {}
        self._nav_items: dict = {}
        self._current = None
        self._build_nav()
        self._navigate("dashboard")
        self._start_alert_poll()

    # ── Layout ────────────────────────────────────────────────────────────
    def _build_layout(self):
        # Header bar
        self.header = tk.Frame(self, bg=COLORS["bg_panel"], height=50)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        logo = tk.Frame(self.header, bg=COLORS["bg_panel"])
        logo.pack(side="left", padx=16)
        tk.Label(logo, text="⚙", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=("Segoe UI Emoji", 18)).pack(side="left")
        tk.Label(logo, text=" SMART INVENTORY ", bg=COLORS["bg_panel"],
                 fg=COLORS["text_primary"], font=FONTS["title"]).pack(side="left")
        tk.Label(logo, text="WAREHOUSE MANAGEMENT SYSTEM", bg=COLORS["bg_panel"],
                 fg=COLORS["text_muted"], font=FONTS["small"]).pack(side="left")

        self.header_right = tk.Frame(self.header, bg=COLORS["bg_panel"])
        self.header_right.pack(side="right", padx=16)
        self.lbl_time = tk.Label(self.header_right, text="", bg=COLORS["bg_panel"],
                                 fg=COLORS["text_muted"], font=FONTS["small"])
        self.lbl_time.pack(side="right")
        self._update_clock()

        # Separator
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

        # Body
        body = tk.Frame(self, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = tk.Frame(body, bg=COLORS["bg_panel"], width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Frame(body, bg=COLORS["border"], width=1).pack(side="left", fill="y")

        # Content
        self.content = tk.Frame(body, bg=COLORS["bg_panel"])
        self.content.pack(side="left", fill="both", expand=True)

    def _update_clock(self):
        from datetime import datetime
        self.lbl_time.config(text=datetime.now().strftime("%a %d %b %Y  %H:%M:%S"))
        self.after(1000, self._update_clock)

    # ── Sidebar Navigation ─────────────────────────────────────────────────
    def _build_nav(self):
        tk.Label(self.sidebar, text="NAVIGATION",
                 bg=COLORS["bg_panel"], fg=COLORS["text_muted"],
                 font=FONTS["badge"]).pack(anchor="w", padx=16, pady=(12, 4))

        nav_items = [
            ("dashboard",       "📊", "Dashboard"),
            ("products",        "📦", "Products"),
            ("stock_tracking",  "📈", "Stock Tracking"),
            ("barcode_scanner", "🔍", "Barcode Scanner"),
            ("suppliers",       "🚚", "Suppliers"),
            ("purchase_orders", "🛒", "Purchase Orders"),
            ("sales",           "💰", "Sales Records"),
            ("alerts",          "🔔", "Alerts"),
            ("analytics",       "📉", "Analytics"),
            ("reports",         "📄", "Export Reports"),
        ]
        for key, icon, label in nav_items:
            item = NavItem(self.sidebar, icon, label,
                           command=lambda k=key: self._navigate(k))
            item.pack(fill="x", pady=1)
            self._nav_items[key] = item

        # Bottom: version
        tk.Label(self.sidebar, text="v1.0.0  |  Industrial Edition",
                 bg=COLORS["bg_panel"], fg=COLORS["text_muted"],
                 font=FONTS["small"]).pack(side="bottom", pady=8)

    # ── Navigation ────────────────────────────────────────────────────────
    def _navigate(self, key: str):
        if self._current == key:
            return
        if self._current:
            self._nav_items[self._current].set_active(False)
        self._current = key
        self._nav_items[key].set_active(True)

        # Clear content
        for w in self.content.winfo_children():
            w.pack_forget()

        if key not in self._modules:
            self._modules[key] = self._create_module(key)

        self._modules[key].pack(fill="both", expand=True)

    def _create_module(self, key: str):
        from modules.products       import ProductsModule
        from modules.stock_tracking import StockTrackingModule
        from modules.barcode_scanner import BarcodeScannerModule
        from modules.suppliers      import SuppliersModule
        from modules.purchase_orders import PurchaseOrdersModule
        from modules.sales          import SalesModule
        from modules.alerts         import AlertsModule
        from modules.analytics      import AnalyticsModule
        from modules.reports        import ReportsModule

        mapping = {
            "dashboard":       lambda: self._make_dashboard(),
            "products":        lambda: ProductsModule(self.content),
            "stock_tracking":  lambda: StockTrackingModule(self.content),
            "barcode_scanner": lambda: BarcodeScannerModule(self.content),
            "suppliers":       lambda: SuppliersModule(self.content),
            "purchase_orders": lambda: PurchaseOrdersModule(self.content),
            "sales":           lambda: SalesModule(self.content),
            "alerts":          lambda: AlertsModule(self.content),
            "analytics":       lambda: AnalyticsModule(self.content),
            "reports":         lambda: ReportsModule(self.content),
        }
        return mapping[key]()

    # ── Dashboard ─────────────────────────────────────────────────────────
    def _make_dashboard(self) -> tk.Frame:
        frame = ttk.Frame(self.content, style="Panel.TFrame")

        tk.Label(frame, text="WAREHOUSE DASHBOARD", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["header"]).pack(
            anchor="w", padx=24, pady=(18, 4))
        tk.Label(frame, text="Real-time warehouse overview and quick actions",
                 bg=COLORS["bg_panel"], fg=COLORS["text_muted"],
                 font=FONTS["label"]).pack(anchor="w", padx=24, pady=(0, 12))

        # KPI row
        kpi_frame = tk.Frame(frame, bg=COLORS["bg_panel"])
        kpi_frame.pack(fill="x", padx=24, pady=8)

        conn = get_connection()
        total_prod  = conn.execute("SELECT COUNT(*) FROM products WHERE status='Active'").fetchone()[0]
        total_stock = conn.execute("SELECT SUM(current_stock) FROM products").fetchone()[0] or 0
        low_stock   = conn.execute("SELECT COUNT(*) FROM products WHERE current_stock<=min_stock AND status='Active'").fetchone()[0]
        total_val   = conn.execute("SELECT SUM(current_stock*cost_price) FROM products WHERE status='Active'").fetchone()[0] or 0
        today_sales = conn.execute("SELECT COALESCE(SUM(total_amount),0) FROM sales_records WHERE status='Completed' AND DATE(sale_date)=DATE('now')").fetchone()[0]
        pending_pos = conn.execute("SELECT COUNT(*) FROM purchase_orders WHERE status IN ('Pending','Ordered')").fetchone()[0]
        suppliers   = conn.execute("SELECT COUNT(*) FROM suppliers WHERE status='Active'").fetchone()[0]
        alerts_cnt  = conn.execute("SELECT COUNT(*) FROM alerts WHERE is_read=0").fetchone()[0]
        conn.close()

        from core.helpers import metric_card
        kpis = [
            ("Total Products",   total_prod,          "active",    COLORS["accent"]),
            ("Total Stock Units",total_stock,          "units",     COLORS["blue"]),
            ("Inventory Value",  f"${total_val:,.0f}", "",          COLORS["green"]),
            ("Today's Sales",    f"${today_sales:,.2f}","",         COLORS["purple"]),
            ("Low Stock Items",  low_stock,            "items",     COLORS["red"]),
            ("Pending POs",      pending_pos,          "orders",    COLORS["yellow"]),
            ("Active Suppliers", suppliers,            "",          COLORS["cyan"]),
            ("Unread Alerts",    alerts_cnt,           "",          COLORS["accent_light"]),
        ]
        for title, val, unit, color in kpis:
            card = metric_card(kpi_frame, title, val, unit, color, width=160)
            card.pack(side="left", padx=6, pady=4, fill="y")

        # Quick actions
        tk.Label(frame, text="▌ QUICK ACTIONS", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["subtitle"]).pack(
            anchor="w", padx=24, pady=(18, 8))
        qa_frame = tk.Frame(frame, bg=COLORS["bg_panel"])
        qa_frame.pack(fill="x", padx=24, pady=4)

        actions = [
            ("+ New Sale",         "Accent.TButton",  lambda: self._navigate("sales")),
            ("+ Purchase Order",   "Blue.TButton",    lambda: self._navigate("purchase_orders")),
            ("+ Add Product",      "Success.TButton", lambda: self._navigate("products")),
            ("🔍 Barcode Scan",     "TButton",         lambda: self._navigate("barcode_scanner")),
            ("📊 View Analytics",  "TButton",         lambda: self._navigate("analytics")),
            ("📄 Export Reports",  "TButton",         lambda: self._navigate("reports")),
        ]
        for lbl, style, cmd in actions:
            ttk.Button(qa_frame, text=lbl, style=style,
                       command=cmd).pack(side="left", padx=6, pady=4)

        # Recent stock alerts
        tk.Label(frame, text="▌ RECENT ALERTS", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["subtitle"]).pack(
            anchor="w", padx=24, pady=(18, 8))

        from core.helpers import make_scrollable_treeview
        tf, tree = make_scrollable_treeview(
            frame,
            ["Type", "Product", "Message", "Time"],
            {"Type": 110, "Product": 180, "Message": 460, "Time": 140},
            height=8)
        tf.pack(fill="x", padx=24, pady=(0, 16))

        conn2 = get_connection()
        alerts = conn2.execute("""SELECT a.alert_type, p.name, a.message, a.created_at
            FROM alerts a LEFT JOIN products p ON p.id=a.product_id
            WHERE a.is_read=0 ORDER BY a.created_at DESC LIMIT 20""").fetchall()
        conn2.close()
        for i, a in enumerate(alerts):
            sev = {"OUT_OF_STOCK": "🔴 Critical",
                   "LOW_STOCK": "🟡 Warning",
                   "REORDER": "🔵 Info"}.get(a["alert_type"], a["alert_type"])
            tag = {"OUT_OF_STOCK": "low",
                   "LOW_STOCK": "warn",
                   "REORDER": "ok"}.get(a["alert_type"], "ok")
            tree.insert("", "end",
                        values=(sev, a["name"] or "—", a["message"], a["created_at"][:16]),
                        tags=(tag,))

        return frame

    # ── Alert polling ──────────────────────────────────────────────────────
    def _start_alert_poll(self):
        def poll():
            n = unread_alert_count()
            self._nav_items["alerts"].set_badge(n)
            self.after(30_000, poll)   # every 30 seconds
        poll()


# ── Bootstrap ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    initialize_database()
    check_and_create_alerts()

    from core.database import get_connection  # needed by dashboard

    app = App()
    app.mainloop()
