"""
modules/analytics.py - Inventory Analytics Dashboard
"""

import tkinter as tk
from tkinter import ttk
from core.database import get_connection
from core.theme import COLORS, FONTS
from core.helpers import section_header, metric_card

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL_OK = True
except ImportError:
    MPL_OK = False


class AnalyticsModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(top, text="INVENTORY ANALYTICS", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(side="left")
        ttk.Button(top, text="⟳ Refresh", command=self._load_data).pack(side="right", padx=4)

        self.period_var = tk.StringVar(value="30")
        pf = ttk.Frame(top, style="Panel.TFrame")
        pf.pack(side="right", padx=12)
        tk.Label(pf, text="Period:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=4)
        ttk.Combobox(pf, textvariable=self.period_var,
                     values=["7", "30", "90", "365"],
                     state="readonly", width=6).pack(side="left")
        self.period_var.trace_add("write", lambda *_: self._load_data())

        # KPI cards row
        self.kpi_frame = tk.Frame(self, bg=COLORS["bg_panel"])
        self.kpi_frame.pack(fill="x", padx=16, pady=8)

        # Notebook for charts
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=4)

        self.tab_overview  = ttk.Frame(nb, style="Panel.TFrame")
        self.tab_stock     = ttk.Frame(nb, style="Panel.TFrame")
        self.tab_sales     = ttk.Frame(nb, style="Panel.TFrame")
        self.tab_valuation = ttk.Frame(nb, style="Panel.TFrame")
        nb.add(self.tab_overview,  text="  Overview  ")
        nb.add(self.tab_stock,     text="  Stock Analysis  ")
        nb.add(self.tab_sales,     text="  Sales Trend  ")
        nb.add(self.tab_valuation, text="  Valuation  ")

    def _load_data(self, *_):
        # Clear KPIs
        for w in self.kpi_frame.winfo_children(): w.destroy()

        days = int(self.period_var.get())
        conn = get_connection()

        total_products = conn.execute("SELECT COUNT(*) FROM products WHERE status='Active'").fetchone()[0]
        total_stock    = conn.execute("SELECT SUM(current_stock) FROM products WHERE status='Active'").fetchone()[0] or 0
        low_count      = conn.execute("SELECT COUNT(*) FROM products WHERE current_stock <= min_stock AND status='Active'").fetchone()[0]
        inv_value      = conn.execute("SELECT SUM(current_stock * cost_price) FROM products WHERE status='Active'").fetchone()[0] or 0
        total_sales    = conn.execute(f"SELECT SUM(total_amount) FROM sales_records WHERE status='Completed' AND sale_date >= datetime('now','-{days} days')").fetchone()[0] or 0
        total_orders   = conn.execute(f"SELECT COUNT(*) FROM sales_records WHERE status='Completed' AND sale_date >= datetime('now','-{days} days')").fetchone()[0]
        total_suppliers= conn.execute("SELECT COUNT(*) FROM suppliers WHERE status='Active'").fetchone()[0]
        pending_pos    = conn.execute("SELECT COUNT(*) FROM purchase_orders WHERE status IN ('Pending','Ordered')").fetchone()[0]

        conn.close()

        kpis = [
            ("Total Products", total_products, "items", COLORS["accent"]),
            ("Total Stock",    total_stock,    "units", COLORS["blue"]),
            ("Inventory Value",f"${inv_value:,.0f}", "",  COLORS["green"]),
            ("Sales (period)", f"${total_sales:,.0f}", "", COLORS["purple"]),
            ("Orders",         total_orders,  "sales", COLORS["cyan"]),
            ("Low Stock",      low_count,     "items", COLORS["red"]),
            ("Suppliers",      total_suppliers,"active",COLORS["yellow"]),
            ("Pending POs",    pending_pos,   "orders",COLORS["accent_light"]),
        ]
        for title, val, unit, color in kpis:
            card = metric_card(self.kpi_frame, title, val, unit, color, width=150)
            card.pack(side="left", padx=6, pady=4, fill="y")

        if MPL_OK:
            self._draw_overview(days)
            self._draw_stock_analysis()
            self._draw_sales_trend(days)
            self._draw_valuation()
        else:
            for tab in [self.tab_overview, self.tab_stock,
                        self.tab_sales, self.tab_valuation]:
                for w in tab.winfo_children(): w.destroy()
                tk.Label(tab, text="Install matplotlib for charts:\npip install matplotlib",
                         bg=COLORS["bg_panel"], fg=COLORS["text_secondary"],
                         font=FONTS["subtitle"]).pack(expand=True)

    # ── Chart helpers ──────────────────────────────────────────────────────
    def _make_fig(self, tab, figsize=(12, 5)):
        for w in tab.winfo_children(): w.destroy()
        fig = Figure(figsize=figsize, facecolor=COLORS["bg_panel"])
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
        return fig, canvas

    def _style_ax(self, ax, title=""):
        ax.set_facecolor(COLORS["bg_card"])
        ax.tick_params(colors=COLORS["text_secondary"], labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS["border"])
        if title:
            ax.set_title(title, color=COLORS["accent"], fontsize=11, pad=8)
        ax.xaxis.label.set_color(COLORS["text_secondary"])
        ax.yaxis.label.set_color(COLORS["text_secondary"])
        ax.grid(axis="y", color=COLORS["border"], linewidth=0.5, alpha=0.5)

    def _draw_overview(self, days):
        fig, canvas = self._make_fig(self.tab_overview, figsize=(13, 5))
        conn = get_connection()

        # Left: Category distribution pie
        ax1 = fig.add_subplot(1, 2, 1)
        cat_data = conn.execute("""SELECT c.name, SUM(p.current_stock)
            FROM products p JOIN categories c ON c.id=p.category_id
            WHERE p.status='Active' GROUP BY c.name ORDER BY 2 DESC""").fetchall()
        if cat_data:
            labels = [r[0] for r in cat_data]
            sizes  = [r[1] for r in cat_data]
            palette = [COLORS["accent"], COLORS["blue"], COLORS["green"],
                       COLORS["purple"], COLORS["cyan"], COLORS["yellow"]]
            ax1.pie(sizes, labels=labels, autopct="%1.0f%%",
                    colors=palette[:len(labels)],
                    textprops={"color": COLORS["text_secondary"], "fontsize": 8},
                    wedgeprops={"edgecolor": COLORS["bg_panel"], "linewidth": 2})
            ax1.set_title("Stock by Category", color=COLORS["accent"], fontsize=11)
            ax1.set_facecolor(COLORS["bg_panel"])

        # Right: Top 10 products by stock value
        ax2 = fig.add_subplot(1, 2, 2)
        val_data = conn.execute("""SELECT name, current_stock * cost_price AS val
            FROM products WHERE status='Active' ORDER BY val DESC LIMIT 10""").fetchall()
        if val_data:
            names = [r[0][:18] for r in val_data]
            vals  = [r[1] for r in val_data]
            bars = ax2.barh(names, vals, color=COLORS["accent"], edgecolor="none")
            self._style_ax(ax2, "Top 10 Products by Value ($)")
        conn.close()
        fig.tight_layout(pad=2)
        canvas.draw()