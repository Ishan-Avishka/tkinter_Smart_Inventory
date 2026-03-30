"""
modules/purchase_orders.py - Purchase Orders Module
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, date, timedelta
from core.database import get_connection
from core.theme import COLORS, FONTS
from core.helpers import (make_scrollable_treeview, search_bar,
                          section_header, confirm_dialog, info_dialog, error_dialog)


class PurchaseOrdersModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        self._build_ui()
        self._load()

    def _build_ui(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(top, text="PURCHASE ORDERS", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(side="left")

        bf = ttk.Frame(top, style="Panel.TFrame")
        bf.pack(side="right")
        ttk.Button(bf, text="＋ New PO", style="Accent.TButton",
                   command=self._new_po).pack(side="left", padx=4)
        ttk.Button(bf, text="✓ Receive", style="Success.TButton",
                   command=self._receive_po).pack(side="left", padx=4)
        ttk.Button(bf, text="👁 View Items", style="Blue.TButton",
                   command=self._view_items).pack(side="left", padx=4)
        ttk.Button(bf, text="🗑 Cancel PO", style="Danger.TButton",
                   command=self._cancel_po).pack(side="left", padx=4)

        sr = ttk.Frame(self, style="Panel.TFrame")
        sr.pack(fill="x", padx=16, pady=4)
        search_bar(sr, self.search_var, "Search PO number, supplier...").pack(side="left")

        tk.Label(sr, text="Status:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(12, 4))
        self.status_var = tk.StringVar(value="All")
        ttk.Combobox(sr, textvariable=self.status_var,
                     values=["All", "Pending", "Ordered", "Partial", "Received", "Cancelled"],
                     state="readonly", width=12).pack(side="left")
        self.status_var.trace_add("write", lambda *_: self._load())

        cols = ["PO Number", "Supplier", "Order Date", "Expected Date",
                "Total Amount", "Status", "Notes"]
        widths = {"PO Number": 120, "Supplier": 180, "Order Date": 110,
                  "Expected Date": 110, "Total Amount": 110, "Status": 90, "Notes": 200}
        tf, self.tree = make_scrollable_treeview(self, cols, widths, height=24)
        tf.pack(fill="both", expand=True, padx=16, pady=(6, 16))
        self.tree.bind("<Double-1>", lambda _: self._view_items())

    def _load(self, *_):
        for r in self.tree.get_children(): self.tree.delete(r)
        q = self.search_var.get().lower()
        status = self.status_var.get()
        sql = """SELECT po.*, s.name AS supplier_name FROM purchase_orders po
                 LEFT JOIN suppliers s ON s.id = po.supplier_id WHERE 1=1"""
        params = []
        if status != "All":
            sql += " AND po.status=?"
            params.append(status)
        conn = get_connection()
        rows = conn.execute(sql + " ORDER BY po.order_date DESC", params).fetchall()
        conn.close()
        for i, r in enumerate(rows):
            vals = (r["po_number"], r["supplier_name"], r["order_date"][:10],
                    (r["expected_date"] or "")[:10], f"${r['total_amount']:,.2f}",
                    r["status"], r["notes"] or "")
            if q and not any(q in str(v).lower() for v in vals):
                continue
            tag = "odd" if i % 2 == 0 else "even"
            if r["status"] == "Pending":   tag = "warn"
            if r["status"] == "Cancelled": tag = "low"
            self.tree.insert("", "end", values=vals, tags=(tag,))

    def _new_po(self):
        PODialog(self, on_save=self._load)

    def _get_selected_po(self):
        sel = self.tree.selection()
        if not sel:
            info_dialog(self, "Select", "Please select a purchase order.")
            return None
        po_num = self.tree.item(sel[0])["values"][0]
        conn = get_connection()
        po = conn.execute("SELECT * FROM purchase_orders WHERE po_number=?",
                          (po_num,)).fetchone()
        conn.close()
        return dict(po) if po else None

    def _receive_po(self):
        po = self._get_selected_po()
        if not po: return
        if po["status"] in ("Received", "Cancelled"):
            info_dialog(self, "Cannot Receive",
                        f"PO is already {po['status']}.")
            return
        if confirm_dialog(self, "Receive PO",
                          f"Mark {po['po_number']} as fully received?\nThis will update stock levels."):
            conn = get_connection()
            items = conn.execute(
                "SELECT * FROM purchase_order_items WHERE po_id=?",
                (po["id"],)).fetchall()
            for item in items:
                qty = item["quantity"]
                conn.execute(
                    "UPDATE products SET current_stock = current_stock + ? WHERE id=?",
                    (qty, item["product_id"]))
                prod = conn.execute("SELECT current_stock FROM products WHERE id=?",
                                    (item["product_id"],)).fetchone()
                conn.execute("""INSERT INTO stock_movements
                    (product_id,movement_type,quantity,reference_id,reference_type,
                     notes,moved_by,stock_before,stock_after)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (item["product_id"], "IN", qty, po["id"], "Purchase Order",
                     f"Received from PO {po['po_number']}", "System",
                     prod["current_stock"] - qty, prod["current_stock"]))
                conn.execute(
                    "UPDATE purchase_order_items SET received_qty=? WHERE id=?",
                    (qty, item["id"]))
            conn.execute(
                "UPDATE purchase_orders SET status='Received', received_date=datetime('now') WHERE id=?",
                (po["id"],))
            conn.commit()
            conn.close()
            self._load()

    def _view_items(self):
        po = self._get_selected_po()
        if not po: return
        POItemsViewer(self, po)

    def _cancel_po(self):
        po = self._get_selected_po()
        if not po: return
        if po["status"] == "Received":
            info_dialog(self, "Cannot Cancel", "Cannot cancel a received PO.")
            return
        if confirm_dialog(self, "Cancel PO", f"Cancel PO {po['po_number']}?"):
            conn = get_connection()
            conn.execute("UPDATE purchase_orders SET status='Cancelled' WHERE id=?",
                         (po["id"],))
            conn.commit()
            conn.close()
            self._load()


class PODialog(tk.Toplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.on_save = on_save
        self.title("New Purchase Order")
        self.configure(bg=COLORS["bg_panel"])
        self.geometry("800x700")
        self.items = []
        self._build()
        self.grab_set()
        self.transient(parent)

    def _build(self):
        section_header(self, "Order Details").pack(fill="x", padx=12, pady=(12, 4))
        hf = tk.Frame(self, bg=COLORS["bg_card"])
        hf.pack(fill="x", padx=12, pady=4)
        hf.columnconfigure(1, weight=1); hf.columnconfigure(3, weight=1)

        conn = get_connection()
        sups = [(r["id"], r["name"]) for r in
                conn.execute("SELECT id,name FROM suppliers WHERE status='Active' ORDER BY name")]
        conn.close()
        self._sup_map = {n: i for i, n in sups}

        tk.Label(hf, text="Supplier*", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=0, column=0, sticky="w", padx=8, pady=6)
        self.v_sup = tk.StringVar()
        ttk.Combobox(hf, textvariable=self.v_sup, values=[n for _, n in sups],
                     state="readonly", width=28, font=FONTS["entry"]).grid(
            row=0, column=1, sticky="ew", padx=8, pady=6)

        tk.Label(hf, text="Expected Date", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=0, column=2, sticky="w", padx=8, pady=6)
        self.v_exp = tk.StringVar(value=str(date.today() + timedelta(days=14)))
        ttk.Entry(hf, textvariable=self.v_exp, width=16, font=FONTS["entry"]).grid(
            row=0, column=3, sticky="ew", padx=8, pady=6)

        tk.Label(hf, text="Notes", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=1, column=0, sticky="w", padx=8, pady=6)
        self.v_notes = tk.StringVar()
        ttk.Entry(hf, textvariable=self.v_notes, width=50, font=FONTS["entry"]).grid(
            row=1, column=1, columnspan=3, sticky="ew", padx=8, pady=6)

        section_header(self, "Order Items").pack(fill="x", padx=12, pady=(12, 4))
        add_row = tk.Frame(self, bg=COLORS["bg_card"])
        add_row.pack(fill="x", padx=12, pady=4)

        conn2 = get_connection()
        prods = [(r["id"], r["sku"], r["name"], r["cost_price"]) for r in
                 conn2.execute("SELECT id,sku,name,cost_price FROM products WHERE status='Active' ORDER BY name")]
        conn2.close()
        self._prod_map = {f"{r[1]} - {r[2]}": (r[0], r[3]) for r in prods}

        tk.Label(add_row, text="Product:", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=8, pady=6)
        self.v_prod = tk.StringVar()
        prod_combo = ttk.Combobox(add_row, textvariable=self.v_prod,
                                  values=list(self._prod_map.keys()),
                                  state="readonly", width=36, font=FONTS["entry"])
        prod_combo.pack(side="left", padx=4)
        prod_combo.bind("<<ComboboxSelected>>", self._on_prod_select)

        tk.Label(add_row, text="Qty:", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(12, 4))
        self.v_qty = tk.StringVar(value="1")
        ttk.Entry(add_row, textvariable=self.v_qty, width=8, font=FONTS["entry"]).pack(side="left")

        tk.Label(add_row, text="Unit Cost $:", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(12, 4))
        self.v_unit_cost = tk.StringVar(value="0.00")
        ttk.Entry(add_row, textvariable=self.v_unit_cost, width=10, font=FONTS["entry"]).pack(side="left")
        ttk.Button(add_row, text="＋ Add Item", style="Accent.TButton",
                   command=self._add_item).pack(side="left", padx=12)

        cols = ["Product", "SKU", "Quantity", "Unit Cost", "Line Total"]
        widths = {"Product": 240, "SKU": 90, "Quantity": 80, "Unit Cost": 100, "Line Total": 110}
        tf, self.items_tree = make_scrollable_treeview(self, cols, widths, height=8)
        tf.pack(fill="both", expand=True, padx=12, pady=4)

        ttk.Button(self, text="🗑 Remove Item", style="Danger.TButton",
                   command=self._remove_item).pack(anchor="e", padx=12)

        total_row = tk.Frame(self, bg=COLORS["bg_panel"])
        total_row.pack(fill="x", padx=12, pady=6)
        tk.Label(total_row, text="TOTAL:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["subtitle"]).pack(side="left", padx=8)
        self.v_total_lbl = tk.Label(total_row, text="$0.00", bg=COLORS["bg_panel"],
                                    fg=COLORS["accent"], font=FONTS["metric_sm"])
        self.v_total_lbl.pack(side="left")

        btn_r = tk.Frame(self, bg=COLORS["bg_panel"])
        btn_r.pack(fill="x", padx=12, pady=12)
        ttk.Button(btn_r, text="✓ Create Purchase Order",
                   style="Accent.TButton", command=self._save).pack(side="right", padx=8)
        ttk.Button(btn_r, text="✕ Cancel", style="Ghost.TButton",
                   command=self.destroy).pack(side="right")

    def _on_prod_select(self, _):
        key = self.v_prod.get()
        if key in self._prod_map:
            self.v_unit_cost.set(f"{self._prod_map[key][1]:.2f}")

    def _add_item(self):
        key = self.v_prod.get()
        if not key:
            error_dialog(self, "Error", "Select a product.")
            return
        try:
            qty = int(self.v_qty.get())
            cost = float(self.v_unit_cost.get())
        except ValueError:
            error_dialog(self, "Error", "Invalid quantity or cost.")
            return
        prod_id, _ = self._prod_map[key]
        sku = key.split(" - ")[0]
        name = " - ".join(key.split(" - ")[1:])
        line = qty * cost
        self.items.append({"product_id": prod_id, "name": name, "sku": sku,
                           "quantity": qty, "unit_cost": cost})
        self.items_tree.insert("", "end",
                               values=(name, sku, qty, f"${cost:.2f}", f"${line:.2f}"))
        total = sum(i["quantity"] * i["unit_cost"] for i in self.items)
        self.v_total_lbl.config(text=f"${total:,.2f}")

    def _remove_item(self):
        sel = self.items_tree.selection()
        if not sel: return
        idx = self.items_tree.index(sel[0])
        self.items.pop(idx)
        self.items_tree.delete(sel[0])
        total = sum(i["quantity"] * i["unit_cost"] for i in self.items)
        self.v_total_lbl.config(text=f"${total:,.2f}")

    def _save(self):
        sup_name = self.v_sup.get()
        if not sup_name:
            error_dialog(self, "Error", "Select a supplier.")
            return
        if not self.items:
            error_dialog(self, "Error", "Add at least one item.")
            return
        sup_id = self._sup_map[sup_name]
        total = sum(i["quantity"] * i["unit_cost"] for i in self.items)
        po_num = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        conn = get_connection()
        cur = conn.execute("""INSERT INTO purchase_orders
            (po_number,supplier_id,expected_date,total_amount,notes,status)
            VALUES (?,?,?,?,?,'Pending')""",
            (po_num, sup_id, self.v_exp.get(), total, self.v_notes.get()))
        po_id = cur.lastrowid
        for item in self.items:
            conn.execute("""INSERT INTO purchase_order_items
                (po_id,product_id,quantity,unit_cost) VALUES (?,?,?,?)""",
                (po_id, item["product_id"], item["quantity"], item["unit_cost"]))
        conn.commit()
        conn.close()
        if self.on_save: self.on_save()
        self.destroy()


class POItemsViewer(tk.Toplevel):
    def __init__(self, parent, po):
        super().__init__(parent)
        self.title(f"PO Items - {po['po_number']}")
        self.configure(bg=COLORS["bg_panel"])
        self.geometry("700x400")
        conn = get_connection()
        items = conn.execute("""
            SELECT p.name, p.sku, poi.quantity, poi.unit_cost, poi.received_qty
            FROM purchase_order_items poi
            JOIN products p ON p.id = poi.product_id
            WHERE poi.po_id=?""", (po["id"],)).fetchall()
        conn.close()

        cols = ["Product Name", "SKU", "Ordered Qty", "Unit Cost", "Received Qty", "Line Total"]
        tf, tree = make_scrollable_treeview(self, cols,
                                            {"Product Name": 220, "SKU": 90,
                                             "Ordered Qty": 90, "Unit Cost": 90,
                                             "Received Qty": 90, "Line Total": 100}, height=15)
        tf.pack(fill="both", expand=True, padx=16, pady=16)
        for i, r in enumerate(items):
            lt = r["quantity"] * r["unit_cost"]
            tree.insert("", "end",
                        values=(r["name"], r["sku"], r["quantity"],
                                f"${r['unit_cost']:.2f}", r["received_qty"],
                                f"${lt:.2f}"),
                        tags=("odd" if i % 2 == 0 else "even",))
        self.grab_set()
