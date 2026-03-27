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

