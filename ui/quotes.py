"""
ui/quotes.py

Quotes screen: list of saved quotes (FR05) plus a Create New Quote form
implementing IPO 2 / the save_quote pseudocode from Criterion 5.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from datetime import date

COLOUR_GREEN = "#00bf63"
COLOUR_WHITE = "#ffffff"
COLOUR_RED = "#ff3131"
COLOUR_BLACK = "#000000"
COLOUR_BG = "#f5f5f5"
FONT_FAMILY = "Canva Sans"


class QuotesScreen(ctk.CTkFrame):
    """
    Self-contained Quotes screen. Manages its own internal navigation
    between the quotes list and the new-quote form, so it can just be
    dropped into the dashboard's content panel.

    Pass in:
        db              - DatabaseManager instance
        start_on_form   - if True, opens straight to the New Quote form
                           (used by the dashboard's "+ New Quote" button)
    """

    def __init__(self, parent, db, start_on_form=False):
        super().__init__(parent, fg_color=COLOUR_BG)
        self.db = db
        self.pack(fill="both", expand=True)

        self.body_frame = ctk.CTkFrame(self, fg_color=COLOUR_BG)
        self.body_frame.pack(fill="both", expand=True)

        # Line item widgets currently on the form: list of dicts
        self.line_item_rows = []
        self.customer_map = {}  # display string -> customer_id

        if start_on_form:
            self._show_new_quote_form()
        else:
            self._show_quote_list()

    def _clear_body(self):
        for widget in self.body_frame.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # Quote list view (FR05, FR09, FR10)
    # ------------------------------------------------------------------

    def _show_quote_list(self):
        self._clear_body()

        header = ctk.CTkFrame(self.body_frame, fg_color=COLOUR_BG)
        header.pack(fill="x", padx=30, pady=(20, 10))

        title = ctk.CTkLabel(
            header, text="Quotes", font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_BLACK
        )
        title.pack(side="left")

        new_quote_btn = ctk.CTkButton(
            header, text="+ New Quote", font=(FONT_FAMILY, 13, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, corner_radius=18,
            height=34, command=self._show_new_quote_form
        )
        new_quote_btn.pack(side="right")

        # Treeview for the quote list
        style = ttk.Style()
        style.configure("Quotes.Treeview", font=(FONT_FAMILY, 11), rowheight=28)
        style.configure("Quotes.Treeview.Heading", font=(FONT_FAMILY, 11, "bold"))

        columns = ("quote_id", "customer", "status", "total", "date")
        tree = ttk.Treeview(
            self.body_frame, columns=columns, show="headings",
            style="Quotes.Treeview", height=15
        )
        tree.heading("quote_id", text="Quote ID")
        tree.heading("customer", text="Customer")
        tree.heading("status", text="Status")
        tree.heading("total", text="Total")
        tree.heading("date", text="Date")

        tree.column("quote_id", width=80, anchor="center")
        tree.column("customer", width=200)
        tree.column("status", width=100, anchor="center")
        tree.column("total", width=100, anchor="e")
        tree.column("date", width=120, anchor="center")

        tree.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        rows = self.db.run_query(
            "SELECT q.quote_id, c.customer_name, q.status, q.total_amount, q.quote_date "
            "FROM Quotes q JOIN Customers c ON q.customer_id = c.customer_id "
            "ORDER BY q.quote_id DESC"
        )
        for quote_id, name, status, total, quote_date in rows:
            tree.insert("", "end", values=(quote_id, name, status, f"${total:.2f}", quote_date))

    # ------------------------------------------------------------------
    # New Quote form (IPO 2)
    # ------------------------------------------------------------------

    def _show_new_quote_form(self):
        self._clear_body()
        self.line_item_rows = []

        # Scrollable frame since the form can grow with many line items
        scroll_frame = ctk.CTkScrollableFrame(self.body_frame, fg_color=COLOUR_BG)
        scroll_frame.pack(fill="both", expand=True, padx=30, pady=20)
        self.form_container = scroll_frame

        title = ctk.CTkLabel(
            scroll_frame, text="New Quote", font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_BLACK
        )
        title.pack(anchor="w", pady=(0, 15))

        # --- Customer selection ---
        customer_row = ctk.CTkFrame(scroll_frame, fg_color=COLOUR_BG)
        customer_row.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            customer_row, text="Customer*", font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK
        ).pack(anchor="w")

        picker_row = ctk.CTkFrame(customer_row, fg_color=COLOUR_BG)
        picker_row.pack(fill="x", pady=(4, 0))

        self.customer_combo = ctk.CTkComboBox(
            picker_row, values=[], font=(FONT_FAMILY, 12), width=320
        )
        self.customer_combo.pack(side="left")
        self._refresh_customer_list()

        add_customer_btn = ctk.CTkButton(
            picker_row, text="+ Add Customer", font=(FONT_FAMILY, 11),
            fg_color="#e0e0e0", text_color=COLOUR_BLACK, hover_color="#cccccc",
            corner_radius=14, height=28, width=110,
            command=self._open_add_customer_dialog
        )
        add_customer_btn.pack(side="left", padx=(10, 0))

        # --- Live totals ---
        self.totals_label = ctk.CTkLabel(
            scroll_frame, text="Total: $0.00", font=(FONT_FAMILY, 16, "bold"), text_color=COLOUR_GREEN
        )

        # --- Error message ---
        self.error_label = ctk.CTkLabel(
            scroll_frame, text="", font=(FONT_FAMILY, 11), text_color=COLOUR_RED
        )

        # --- Line items ---
        ctk.CTkLabel(
            scroll_frame, text="Line Items*", font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK
        ).pack(anchor="w", pady=(10, 4))

        self.line_items_frame = ctk.CTkFrame(scroll_frame, fg_color=COLOUR_WHITE, corner_radius=10)
        self.line_items_frame.pack(fill="x")

        self._add_line_item_row()  # start with one row

        add_line_btn = ctk.CTkButton(
            scroll_frame, text="+ Add Line Item", font=(FONT_FAMILY, 12),
            fg_color="#e0e0e0", text_color=COLOUR_BLACK, hover_color="#cccccc",
            corner_radius=14, height=30, command=self._add_line_item_row
        )
        add_line_btn.pack(anchor="w", pady=(8, 15))

        # --- Notes ---
        ctk.CTkLabel(
            scroll_frame, text="Notes (optional)", font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK
        ).pack(anchor="w")
        self.notes_entry = ctk.CTkTextbox(scroll_frame, height=60, font=(FONT_FAMILY, 12))
        self.notes_entry.pack(fill="x", pady=(4, 15))

        # Now place the totals and error labels (created earlier) into the layout
        self.totals_label.pack(anchor="e", pady=(0, 15))
        self.error_label.pack(anchor="w")

        # --- Buttons ---
        button_row = ctk.CTkFrame(scroll_frame, fg_color=COLOUR_BG)
        button_row.pack(fill="x", pady=(10, 20))

        cancel_btn = ctk.CTkButton(
            button_row, text="Cancel", font=(FONT_FAMILY, 13),
            fg_color="#e0e0e0", text_color=COLOUR_BLACK, hover_color="#cccccc",
            corner_radius=18, height=36, width=100,
            command=self._show_quote_list
        )
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(
            button_row, text="Save Quote", font=(FONT_FAMILY, 13, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK,
            corner_radius=18, height=36, width=140,
            command=self._save_quote
        )
        save_btn.pack(side="right")

    def _refresh_customer_list(self):
        rows = self.db.run_query(
            "SELECT customer_id, customer_name, vehicle_rego FROM Customers ORDER BY customer_name"
        )
        self.customer_map = {}
        display_values = []
        for customer_id, name, rego in rows:
            display = f"{name} ({rego})"
            self.customer_map[display] = customer_id
            display_values.append(display)

        self.customer_combo.configure(values=display_values)
        if display_values:
            self.customer_combo.set(display_values[-1])  # most recently added
        else:
            self.customer_combo.set("")

    # ------------------------------------------------------------------
    # Line item rows
    # ------------------------------------------------------------------

    def _add_line_item_row(self):
        row_frame = ctk.CTkFrame(self.line_items_frame, fg_color=COLOUR_WHITE)
        row_frame.pack(fill="x", padx=10, pady=6)

        desc_entry = ctk.CTkEntry(row_frame, placeholder_text="Description", font=(FONT_FAMILY, 11), width=200)
        desc_entry.pack(side="left", padx=(0, 6))

        qty_entry = ctk.CTkEntry(row_frame, placeholder_text="Qty", font=(FONT_FAMILY, 11), width=60)
        qty_entry.pack(side="left", padx=(0, 6))

        price_entry = ctk.CTkEntry(row_frame, placeholder_text="Unit price", font=(FONT_FAMILY, 11), width=90)
        price_entry.pack(side="left", padx=(0, 6))

        type_combo = ctk.CTkComboBox(row_frame, values=["Parts", "Labour"], font=(FONT_FAMILY, 11), width=100)
        type_combo.set("Parts")
        type_combo.pack(side="left", padx=(0, 6))

        remove_btn = ctk.CTkButton(
            row_frame, text="✕", width=28, height=28, corner_radius=14,
            fg_color=COLOUR_RED, text_color=COLOUR_WHITE, hover_color="#cc2020",
            font=(FONT_FAMILY, 12),
            command=lambda: self._remove_line_item_row(row_frame, row_data)
        )
        remove_btn.pack(side="left", padx=(0, 6))

        confirm_btn = ctk.CTkButton(
            row_frame, text="✓", width=28, height=28, corner_radius=14,
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, hover_color="#00a855",
            font=(FONT_FAMILY, 12),
            command=lambda: self._confirm_line_item_row(row_data)
        )
        confirm_btn.pack(side="left")

        # Recalculate totals whenever qty/price changes
        qty_entry.bind("<KeyRelease>", lambda e: self._recalculate_totals())
        price_entry.bind("<KeyRelease>", lambda e: self._recalculate_totals())
        type_combo.configure(command=lambda choice: self._recalculate_totals())

        row_data = {
            "frame": row_frame,
            "description": desc_entry,
            "quantity": qty_entry,
            "unit_price": price_entry,
            "item_type": type_combo,
            "confirm_btn": confirm_btn,
            "confirmed": False,
        }
        self.line_item_rows.append(row_data)
        self._recalculate_totals()

    def _confirm_line_item_row(self, row_data):
        """Validate and lock in a single line item row, matching the
        explicit submit pattern used in the Add Customer dialog."""
        description = row_data["description"].get().strip()
        qty_str = row_data["quantity"].get().strip()
        price_str = row_data["unit_price"].get().strip()

        if not description or not qty_str or not price_str:
            self.error_label.configure(text="Fill in description, quantity and price before confirming")
            return

        try:
            quantity = float(qty_str)
            unit_price = float(price_str)
        except ValueError:
            self.error_label.configure(text="Quantity and unit price must be numbers")
            return

        if quantity <= 0 or unit_price < 0:
            self.error_label.configure(text="Quantity must be > 0 and price must be >= 0")
            return

        # Lock the row so it can't be accidentally edited after confirming
        row_data["description"].configure(state="disabled")
        row_data["quantity"].configure(state="disabled")
        row_data["unit_price"].configure(state="disabled")
        row_data["item_type"].configure(state="disabled")
        row_data["confirm_btn"].configure(state="disabled", fg_color="#cccccc", text="Confirmed")
        row_data["confirmed"] = True
        self.error_label.configure(text="")
        self._recalculate_totals()

    def _remove_line_item_row(self, row_frame, row_data):
        if len(self.line_item_rows) <= 1:
            self.error_label.configure(text="A quote needs at least one line item")
            return
        row_frame.destroy()
        self.line_item_rows.remove(row_data)
        self._recalculate_totals()

    def _recalculate_totals(self):
        total_parts = 0.0
        total_labour = 0.0

        for row in self.line_item_rows:
            try:
                qty = float(row["quantity"].get())
                price = float(row["unit_price"].get())
            except ValueError:
                continue  # incomplete row, skip for live total purposes

            line_total = qty * price
            if row["item_type"].get() == "Parts":
                total_parts += line_total
            else:
                total_labour += line_total

        total = total_parts + total_labour
        self.totals_label.configure(text=f"Total: ${total:.2f}")

    # ------------------------------------------------------------------
    # Add customer dialog
    # ------------------------------------------------------------------

    def _open_add_customer_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Customer")
        dialog.geometry("380x520")
        dialog.grab_set()  # modal

        scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color=COLOUR_BG)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        fields = {}
        field_specs = [
            ("customer_name", "Full Name*"),
            ("phone", "Phone*"),
            ("email", "Email"),
            ("vehicle_make", "Vehicle Make*"),
            ("vehicle_model", "Vehicle Model*"),
            ("vehicle_year", "Vehicle Year*"),
            ("vehicle_rego", "Rego*"),
        ]

        for key, label_text in field_specs:
            ctk.CTkLabel(scroll_frame, text=label_text, font=(FONT_FAMILY, 11)).pack(anchor="w", pady=(8, 0))
            entry = ctk.CTkEntry(scroll_frame, font=(FONT_FAMILY, 11), width=300)
            entry.pack()
            fields[key] = entry

        error_label = ctk.CTkLabel(scroll_frame, text="", font=(FONT_FAMILY, 10), text_color=COLOUR_RED)
        error_label.pack(pady=(6, 0))

        def save_customer():
            name = fields["customer_name"].get().strip()
            phone = fields["phone"].get().strip()
            email = fields["email"].get().strip() or None
            make = fields["vehicle_make"].get().strip()
            model = fields["vehicle_model"].get().strip()
            year_str = fields["vehicle_year"].get().strip()
            rego = fields["vehicle_rego"].get().strip()

            if not all([name, phone, make, model, year_str, rego]):
                error_label.configure(text="Please fill in all required fields")
                return

            try:
                year = int(year_str)
            except ValueError:
                error_label.configure(text="Vehicle year must be a number")
                return

            self.db.run_update(
                "INSERT INTO Customers (customer_name, phone, email, vehicle_make, "
                "vehicle_model, vehicle_year, vehicle_rego) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, phone, email, make, model, year, rego)
            )
            self._refresh_customer_list()
            dialog.destroy()

        save_btn = ctk.CTkButton(
            dialog, text="Save Customer", font=(FONT_FAMILY, 12, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK,
            corner_radius=16, height=36, command=save_customer
        )
        save_btn.pack(pady=(0, 15))

    # ------------------------------------------------------------------
    # Save quote (pseudocode: save_quote)
    # ------------------------------------------------------------------

    def _save_quote(self):
        customer_display = self.customer_combo.get()
        if customer_display not in self.customer_map:
            self.error_label.configure(text="Select a customer")
            return
        customer_id = self.customer_map[customer_display]

        # Validate and collect line items
        parsed_items = []
        for row in self.line_item_rows:
            description = row["description"].get().strip()
            qty_str = row["quantity"].get().strip()
            price_str = row["unit_price"].get().strip()
            item_type = row["item_type"].get()

            if not description or not qty_str or not price_str:
                self.error_label.configure(text="Invalid line item - all fields are required")
                return

            try:
                quantity = float(qty_str)
                unit_price = float(price_str)
            except ValueError:
                self.error_label.configure(text="Quantity and unit price must be numbers")
                return

            if quantity <= 0 or unit_price < 0:
                self.error_label.configure(text="Invalid line item - check quantity and price")
                return

            line_total = quantity * unit_price
            parsed_items.append({
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
                "item_type": item_type,
                "line_total": line_total,
            })

        if not parsed_items:
            self.error_label.configure(text="Add at least one line item")
            return

        total_parts = sum(i["line_total"] for i in parsed_items if i["item_type"] == "Parts")
        total_labour = sum(i["line_total"] for i in parsed_items if i["item_type"] == "Labour")
        total_amount = total_parts + total_labour
        notes = self.notes_entry.get("1.0", "end").strip() or None
        quote_date = date.today().strftime("%d-%m-%Y")

        quote_id = self.db.run_update(
            "INSERT INTO Quotes (customer_id, quote_date, status, total_parts, "
            "total_labour, total_amount, notes) VALUES (?, ?, 'Pending', ?, ?, ?, ?)",
            (customer_id, quote_date, total_parts, total_labour, total_amount, notes)
        )

        for item in parsed_items:
            self.db.run_update(
                "INSERT INTO QuoteLineItems (quote_id, description, quantity, "
                "unit_price, item_type, line_total) VALUES (?, ?, ?, ?, ?, ?)",
                (quote_id, item["description"], item["quantity"],
                 item["unit_price"], item["item_type"], item["line_total"])
            )

        self.error_label.configure(text="")
        self._show_quote_list()