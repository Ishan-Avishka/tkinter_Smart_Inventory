"""
modules/suppliers.py - Supplier Management Module
"""

import tkinter as tk
from tkinter import ttk
from core.database import get_connection
from core.theme import COLORS, FONTS
from core.helpers import (make_scrollable_treeview, search_bar,
                          section_header, confirm_dialog, info_dialog, error_dialog)


class SuppliersModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        self._build_ui()
        self._load()

    def _build_ui(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(top, text="SUPPLIER MANAGEMENT", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(side="left")

        btn_f = ttk.Frame(top, style="Panel.TFrame")
        btn_f.pack(side="right")
        ttk.Button(btn_f, text="＋ Add Supplier",
                   style="Accent.TButton", command=self._add).pack(side="left", padx=4)
        ttk.Button(btn_f, text="✎ Edit",
                   style="Blue.TButton", command=self._edit).pack(side="left", padx=4)
        ttk.Button(btn_f, text="🗑 Delete",
                   style="Danger.TButton", command=self._delete).pack(side="left", padx=4)

        sr = ttk.Frame(self, style="Panel.TFrame")
        sr.pack(fill="x", padx=16, pady=4)
        search_bar(sr, self.search_var, "Search suppliers...").pack(side="left")

        tk.Label(sr, text="Status:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(12, 4))
        self.status_var = tk.StringVar(value="All")
        ttk.Combobox(sr, textvariable=self.status_var,
                     values=["All", "Active", "Inactive"],
                     state="readonly", width=10).pack(side="left")
        self.status_var.trace_add("write", lambda *_: self._load())

        cols = ["ID", "Name", "Contact Person", "Email", "Phone",
                "City", "Country", "Payment Terms", "Status"]
        widths = {"ID": 50, "Name": 180, "Contact Person": 140, "Email": 180,
                  "Phone": 120, "City": 100, "Country": 90,
                  "Payment Terms": 110, "Status": 80}
        tf, self.tree = make_scrollable_treeview(self, cols, widths, height=24)
        tf.pack(fill="both", expand=True, padx=16, pady=(6, 16))
        self.tree.bind("<Double-1>", lambda _: self._edit())

    def _load(self, *_):
        for r in self.tree.get_children():
            self.tree.delete(r)
        q = self.search_var.get().lower()
        status = self.status_var.get()
        sql = "SELECT * FROM suppliers WHERE 1=1"
        params = []
        if status != "All":
            sql += " AND status=?"
            params.append(status)
        conn = get_connection()
        rows = conn.execute(sql + " ORDER BY name", params).fetchall()
        conn.close()
        for i, r in enumerate(rows):
            vals = (r["id"], r["name"], r["contact_person"] or "—",
                    r["email"] or "—", r["phone"] or "—",
                    r["city"] or "—", r["country"] or "—",
                    r["payment_terms"] or "—", r["status"])
            if q and not any(q in str(v).lower() for v in vals):
                continue
            tag = "odd" if i % 2 == 0 else "even"
            self.tree.insert("", "end", values=vals, tags=(tag,))

    def _add(self):
        SupplierDialog(self, on_save=self._load)

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            info_dialog(self, "Select", "Select a supplier first.")
            return
        sid = self.tree.item(sel[0])["values"][0]
        conn = get_connection()
        sup = conn.execute("SELECT * FROM suppliers WHERE id=?", (sid,)).fetchone()
        conn.close()
        if sup:
            SupplierDialog(self, supplier=dict(sup), on_save=self._load)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            info_dialog(self, "Select", "Select a supplier first.")
            return
        sid = self.tree.item(sel[0])["values"][0]
        name = self.tree.item(sel[0])["values"][1]
        if confirm_dialog(self, "Delete Supplier", f"Delete supplier '{name}'?"):
            conn = get_connection()
            conn.execute("DELETE FROM suppliers WHERE id=?", (sid,))
            conn.commit()
            conn.close()
            self._load()


class SupplierDialog(tk.Toplevel):
    def __init__(self, parent, supplier=None, on_save=None):
        super().__init__(parent)
        self.supplier = supplier
        self.on_save = on_save
        self.title("Supplier" if not supplier else f"Edit: {supplier['name']}")
        self.configure(bg=COLORS["bg_panel"])
        self.geometry("560x560")
        self.resizable(False, False)
        self._build()
        self.grab_set()
        self.transient(parent)

    def _row(self, frame, label, row, col=0, width=26, value=""):
        tk.Label(frame, text=label, bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=row, column=col, sticky="w", padx=8, pady=5)
        var = tk.StringVar(value=str(value) if value else "")
        ttk.Entry(frame, textvariable=var, width=width,
                  font=FONTS["entry"]).grid(
            row=row, column=col + 1, sticky="ew", padx=8, pady=5)
        return var

    def _build(self):
        p = self.supplier or {}
        section_header(self, "Supplier Information").pack(fill="x", padx=12, pady=(12, 4))
        f = tk.Frame(self, bg=COLORS["bg_card"])
        f.pack(fill="x", padx=12, pady=4)
        f.columnconfigure(1, weight=1); f.columnconfigure(3, weight=1)

        self.v_name    = self._row(f, "Company Name*", 0, 0, value=p.get("name", ""))
        self.v_contact = self._row(f, "Contact Person", 1, 0, value=p.get("contact_person", ""))
        self.v_email   = self._row(f, "Email", 2, 0, value=p.get("email", ""))
        self.v_phone   = self._row(f, "Phone", 3, 0, value=p.get("phone", ""))
        self.v_city    = self._row(f, "City", 0, 2, value=p.get("city", ""))
        self.v_country = self._row(f, "Country", 1, 2, value=p.get("country", ""))
        self.v_terms   = self._row(f, "Payment Terms", 2, 2, value=p.get("payment_terms", "Net 30"))

        tk.Label(f, text="Status", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=3, column=2, sticky="w", padx=8, pady=5)
        self.v_status = tk.StringVar(value=p.get("status", "Active"))
        ttk.Combobox(f, textvariable=self.v_status,
                     values=["Active", "Inactive"], state="readonly", width=14).grid(
            row=3, column=3, sticky="ew", padx=8, pady=5)

        section_header(self, "Address & Notes").pack(fill="x", padx=12, pady=(12, 4))
        nf = tk.Frame(self, bg=COLORS["bg_card"])
        nf.pack(fill="x", padx=12, pady=4)
        tk.Label(nf, text="Address", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(anchor="w", padx=8, pady=(8, 2))
        self.txt_addr = tk.Text(nf, height=2, bg=COLORS["bg_input"],
                                fg=COLORS["text_primary"], font=FONTS["entry"],
                                insertbackground=COLORS["accent"], relief="flat", padx=6)
        self.txt_addr.pack(fill="x", padx=8, pady=(0, 4))
        if p.get("address"): self.txt_addr.insert("1.0", p["address"])

        tk.Label(nf, text="Notes", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(anchor="w", padx=8, pady=(4, 2))
        self.txt_notes = tk.Text(nf, height=3, bg=COLORS["bg_input"],
                                 fg=COLORS["text_primary"], font=FONTS["entry"],
                                 insertbackground=COLORS["accent"], relief="flat", padx=6)
        self.txt_notes.pack(fill="x", padx=8, pady=(0, 8))
        if p.get("notes"): self.txt_notes.insert("1.0", p["notes"])

        btn_r = tk.Frame(self, bg=COLORS["bg_panel"])
        btn_r.pack(fill="x", padx=12, pady=12)
        ttk.Button(btn_r, text="✓ Save", style="Accent.TButton",
                   command=self._save).pack(side="right", padx=8)
        ttk.Button(btn_r, text="✕ Cancel", style="Ghost.TButton",
                   command=self.destroy).pack(side="right")

    def _save(self):
        name = self.v_name.get().strip()
        if not name:
            error_dialog(self, "Error", "Company name is required.")
            return
        params = (name, self.v_contact.get(), self.v_email.get(),
                  self.v_phone.get(), self.txt_addr.get("1.0", "end").strip(),
                  self.v_city.get(), self.v_country.get(),
                  self.v_terms.get(), self.txt_notes.get("1.0", "end").strip(),
                  self.v_status.get())
        conn = get_connection()
        if self.supplier:
            conn.execute("""UPDATE suppliers SET name=?,contact_person=?,email=?,phone=?,
                address=?,city=?,country=?,payment_terms=?,notes=?,status=? WHERE id=?""",
                         params + (self.supplier["id"],))
        else:
            conn.execute("""INSERT INTO suppliers
                (name,contact_person,email,phone,address,city,country,payment_terms,notes,status)
                VALUES (?,?,?,?,?,?,?,?,?,?)""", params)
        conn.commit()
        conn.close()
        if self.on_save: self.on_save()
        self.destroy()
