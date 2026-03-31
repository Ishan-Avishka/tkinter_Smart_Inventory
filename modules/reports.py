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