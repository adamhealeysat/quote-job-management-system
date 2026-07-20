"""
ui/quotes.py

Quotes screen: list of saved quotes (FR05) plus a Create New Quote form
implementing IPO 2 / the save_quote pseudocode from Criterion 5.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from datetime import date, datetime

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

    def __init__(self, parent, db, start_on_form=False, on_convert_to_job=None):
        super().__init__(parent, fg_color=COLOUR_BG)
        self.db = db
        self.on_convert_to_job = on_convert_to_job
        self.pack(fill="both", expand=True)

        self.body_frame = ctk.CTkFrame(self, fg_color=COLOUR_BG)
        self.body_frame.pack(fill="both", expand=True)

        # Line item widgets currently on the form: list of dicts
        self.line_item_rows = []
        self.customer_map = {}  # display string -> customer_id
        self.edit_quote_id = None  # None = creating a new quote, else editing
        self.all_quote_rows = []  # full unfiltered dataset for search
        self.selected_quote_id = None

        if start_on_form:
            self._show_quote_form()
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
        self.selected_quote_id = None

        header = ctk.CTkFrame(self.body_frame, fg_color=COLOUR_BG)
        header.pack(fill="x", padx=30, pady=(20, 10))

        title = ctk.CTkLabel(
            header, text="Quotes", font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_BLACK
        )
        title.pack(side="left")

        new_quote_btn = ctk.CTkButton(
            header, text="+ New Quote", font=(FONT_FAMILY, 13, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, corner_radius=18,
            height=34, command=lambda: self._show_quote_form()
        )
        new_quote_btn.pack(side="right")

        # --- Search bar (FR09: customer name, vehicle details, quote ID or status) ---
        search_row = ctk.CTkFrame(self.body_frame, fg_color=COLOUR_BG)
        search_row.pack(fill="x", padx=30, pady=(0, 10))

        self.quote_search_entry = ctk.CTkEntry(
            search_row, placeholder_text="Search by customer, vehicle, quote ID or status",
            font=(FONT_FAMILY, 12), width=360
        )
        self.quote_search_entry.pack(side="left")
        self.quote_search_entry.bind("<KeyRelease>", lambda e: self._filter_quotes())

        self.quote_result_label = ctk.CTkLabel(
            search_row, text="", font=(FONT_FAMILY, 11), text_color="#888888"
        )
        self.quote_result_label.pack(side="left", padx=(10, 0))

        # Treeview for the quote list
        style = ttk.Style()
        style.configure("Quotes.Treeview", font=(FONT_FAMILY, 11), rowheight=28)
        style.configure("Quotes.Treeview.Heading", font=(FONT_FAMILY, 11, "bold"))

        columns = ("quote_id", "customer", "status", "total", "date")
        self.quote_tree = ttk.Treeview(
            self.body_frame, columns=columns, show="headings",
            style="Quotes.Treeview", height=10
        )

        # Column heading labels and click-to-sort bindings (FR10)
        heading_labels = {
            "quote_id": "Quote ID", "customer": "Customer",
            "status": "Status", "total": "Total", "date": "Date"
        }
        for col, label in heading_labels.items():
            self.quote_tree.heading(col, text=label, command=lambda c=col: self._sort_quotes(c))

        self.quote_tree.column("quote_id", width=80, anchor="center")
        self.quote_tree.column("customer", width=200)
        self.quote_tree.column("status", width=100, anchor="center")
        self.quote_tree.column("total", width=100, anchor="e")
        self.quote_tree.column("date", width=120, anchor="center")

        self.quote_tree.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        self.quote_tree.bind("<Double-1>", self._on_quote_row_double_click)
        self.quote_tree.bind("<<TreeviewSelect>>", self._on_quote_row_select)

        hint_label = ctk.CTkLabel(
            self.body_frame, text="Double-click a quote to view or edit it",
            font=(FONT_FAMILY, 10), text_color="#888888"
        )
        hint_label.pack(padx=30, pady=(0, 5), anchor="w")

        action_row = ctk.CTkFrame(self.body_frame, fg_color=COLOUR_BG)
        action_row.pack(fill="x", padx=30, pady=(0, 15))

        self.convert_btn = ctk.CTkButton(
            action_row, text="Convert to Job", font=(FONT_FAMILY, 12, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, hover_color="#00a855",
            corner_radius=16, height=32, width=140, state="disabled",
            command=self._convert_selected_quote_to_job
        )
        self.convert_btn.pack(side="left")

        self.convert_message_label = ctk.CTkLabel(
            action_row, text="", font=(FONT_FAMILY, 11), text_color=COLOUR_RED
        )
        self.convert_message_label.pack(side="left", padx=(10, 0))

        # Load full dataset, including vehicle details for search (FR09)
        self.all_quote_rows = self.db.run_query(
            "SELECT q.quote_id, c.customer_name, q.status, q.total_amount, q.quote_date, "
            "c.vehicle_make, c.vehicle_model, c.vehicle_rego "
            "FROM Quotes q JOIN Customers c ON q.customer_id = c.customer_id"
        )
        self.quote_rows = list(self.all_quote_rows)

        # Default sort: Quote ID ascending
        self.sort_column = "quote_id"
        self.sort_reverse = False
        self._apply_sort()
        self._populate_quote_tree()

    def _on_quote_row_double_click(self, event):
        selection = self.quote_tree.selection()
        if not selection:
            return
        values = self.quote_tree.item(selection[0], "values")
        quote_id = int(values[0])
        self._show_quote_form(quote_id)

    def _on_quote_row_select(self, event):
        selection = self.quote_tree.selection()
        if not selection:
            self.selected_quote_id = None
            self.convert_btn.configure(state="disabled")
            return
        values = self.quote_tree.item(selection[0], "values")
        self.selected_quote_id = int(values[0])
        self.convert_btn.configure(state="normal")
        self.convert_message_label.configure(text="")

    def _convert_selected_quote_to_job(self):
        """Convert an Accepted quote into an active Job record (IPO 3)."""
        if self.selected_quote_id is None:
            return

        rows = self.db.run_query(
            "SELECT customer_id, status FROM Quotes WHERE quote_id = ?",
            (self.selected_quote_id,)
        )
        if not rows:
            self.convert_message_label.configure(text="Quote not found")
            return
        customer_id, status = rows[0]

        # IPO 3: validate quote status is Accepted before converting
        if status != "Accepted":
            self.convert_message_label.configure(
                text="Please accept this quote before converting it to a job"
            )
            return

        # Avoid creating a duplicate job from the same quote
        existing_job = self.db.run_query(
            "SELECT job_id FROM Jobs WHERE quote_id = ?", (self.selected_quote_id,)
        )
        if existing_job:
            self.convert_message_label.configure(
                text=f"A job (#{existing_job[0][0]}) already exists for this quote"
            )
            return

        job_date = date.today().strftime("%d-%m-%Y")
        job_id = self.db.run_update(
            "INSERT INTO Jobs (quote_id, customer_id, job_date, status) "
            "VALUES (?, ?, ?, 'Pending')",
            (self.selected_quote_id, customer_id, job_date)
        )

        if self.on_convert_to_job:
            self.on_convert_to_job(job_id)
        else:
            self._show_quote_list()

    def _filter_quotes(self):
        term = self.quote_search_entry.get().strip().lower()
        if not term:
            self.quote_rows = list(self.all_quote_rows)
        else:
            def matches(row):
                quote_id, name, status, total, quote_date, make, model, rego = row
                haystack = f"{quote_id} {name} {status} {make} {model} {rego}".lower()
                return term in haystack
            self.quote_rows = [r for r in self.all_quote_rows if matches(r)]

        self._apply_sort()
        self._populate_quote_tree()

        if term and not self.quote_rows:
            self.quote_result_label.configure(text="No results found")
        elif term:
            self.quote_result_label.configure(text=f"{len(self.quote_rows)} result(s)")
        else:
            self.quote_result_label.configure(text="")

    def _populate_quote_tree(self):
        """Re-render the Treeview rows from self.quote_rows in current sort order."""
        self.quote_tree.delete(*self.quote_tree.get_children())
        for row in self.quote_rows:
            quote_id, name, status, total, quote_date = row[0], row[1], row[2], row[3], row[4]
            self.quote_tree.insert(
                "", "end", values=(quote_id, name, status, f"${total:.2f}", quote_date)
            )
        self._update_sort_indicators()

    def _apply_sort(self):
        """Sort self.quote_rows using the current self.sort_column/self.sort_reverse
        without changing them (used after filtering, and by _sort_quotes)."""
        col_index = {"quote_id": 0, "customer": 1, "status": 2, "total": 3, "date": 4}[self.sort_column]

        def sort_key(row):
            value = row[col_index]
            if self.sort_column == "date":
                try:
                    return datetime.strptime(value, "%d-%m-%Y")
                except (ValueError, TypeError):
                    return datetime.min
            if self.sort_column in ("customer", "status"):
                return str(value).lower()
            return value

        self.quote_rows = sorted(self.quote_rows, key=sort_key, reverse=self.sort_reverse)

    def _sort_quotes(self, column):
        """Handle a column header click: toggle direction if already sorted
        by this column, otherwise switch to it using its sensible default
        direction (FR10).
        """
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            # Date defaults to newest-first (reverse); everything else ascending
            self.sort_reverse = (column == "date")

        self._apply_sort()
        self._populate_quote_tree()

    def _update_sort_indicators(self):
        """Show an arrow on the currently sorted column's heading."""
        heading_labels = {
            "quote_id": "Quote ID", "customer": "Customer",
            "status": "Status", "total": "Total", "date": "Date"
        }
        for col, label in heading_labels.items():
            if col == self.sort_column:
                arrow = " ▼" if self.sort_reverse else " ▲"
                self.quote_tree.heading(col, text=label + arrow)
            else:
                self.quote_tree.heading(col, text=label)

    # ------------------------------------------------------------------
    # New Quote form (IPO 2)
    # ------------------------------------------------------------------

    def _show_quote_form(self, quote_id=None):
        self._clear_body()
        self.line_item_rows = []
        self.edit_quote_id = quote_id
        is_edit = quote_id is not None

        existing_quote = None
        existing_items = []
        if is_edit:
            rows = self.db.run_query(
                "SELECT customer_id, status, notes FROM Quotes WHERE quote_id = ?",
                (quote_id,)
            )
            if rows:
                existing_quote = rows[0]
            existing_items = self.db.run_query(
                "SELECT description, quantity, unit_price, item_type "
                "FROM QuoteLineItems WHERE quote_id = ?",
                (quote_id,)
            )

        # Scrollable frame since the form can grow with many line items
        scroll_frame = ctk.CTkScrollableFrame(self.body_frame, fg_color=COLOUR_BG)
        scroll_frame.pack(fill="both", expand=True, padx=30, pady=20)
        self.form_container = scroll_frame

        title = ctk.CTkLabel(
            scroll_frame, text=f"Edit Quote #{quote_id}" if is_edit else "New Quote",
            font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_BLACK
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

        add_customer_btn = ctk.CTkButton(
            picker_row, text="+ Add Customer", font=(FONT_FAMILY, 11),
            fg_color="#e0e0e0", text_color=COLOUR_BLACK, hover_color="#cccccc",
            corner_radius=14, height=28, width=110,
            command=self._open_add_customer_dialog
        )
        add_customer_btn.pack(side="left", padx=(10, 0))

        existing_customer_id = existing_quote[0] if existing_quote else None
        self._refresh_customer_list(select_customer_id=existing_customer_id)

        # --- Status selection (Pending / Accepted / Declined) ---
        status_row = ctk.CTkFrame(scroll_frame, fg_color=COLOUR_BG)
        status_row.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            status_row, text="Status", font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK
        ).pack(anchor="w")

        self.status_combo = ctk.CTkComboBox(
            status_row, values=["Pending", "Accepted", "Declined"],
            font=(FONT_FAMILY, 12), width=200
        )
        self.status_combo.set(existing_quote[1] if existing_quote else "Pending")
        self.status_combo.pack(anchor="w", pady=(4, 0))

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

        if existing_items:
            for description, quantity, unit_price, item_type in existing_items:
                self._add_line_item_row(prefill={
                    "description": description, "quantity": quantity,
                    "unit_price": unit_price, "item_type": item_type
                })
        else:
            self._add_line_item_row()  # start with one blank row

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
        if existing_quote and existing_quote[2]:
            self.notes_entry.insert("1.0", existing_quote[2])

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
            button_row, text="Save Changes" if is_edit else "Save Quote",
            font=(FONT_FAMILY, 13, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK,
            corner_radius=18, height=36, width=140,
            command=self._save_quote
        )
        save_btn.pack(side="right")

    def _refresh_customer_list(self, select_customer_id=None):
        rows = self.db.run_query(
            "SELECT customer_id, customer_name, vehicle_rego FROM Customers ORDER BY customer_name"
        )
        self.customer_map = {}
        id_to_display = {}
        display_values = []
        for customer_id, name, rego in rows:
            display = f"{name} ({rego})"
            self.customer_map[display] = customer_id
            id_to_display[customer_id] = display
            display_values.append(display)

        self.customer_combo.configure(values=display_values)
        if select_customer_id is not None and select_customer_id in id_to_display:
            self.customer_combo.set(id_to_display[select_customer_id])
        elif display_values:
            self.customer_combo.set(display_values[-1])  # most recently added
        else:
            self.customer_combo.set("")

    # ------------------------------------------------------------------
    # Line item rows
    # ------------------------------------------------------------------

    def _add_line_item_row(self, prefill=None):
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

        if prefill:
            desc_entry.insert(0, prefill["description"])
            qty_entry.insert(0, str(prefill["quantity"]))
            price_entry.insert(0, str(prefill["unit_price"]))
            type_combo.set(prefill["item_type"])

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
        status = self.status_combo.get()

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

        if self.edit_quote_id is None:
            # Creating a new quote
            quote_date = date.today().strftime("%d-%m-%Y")
            quote_id = self.db.run_update(
                "INSERT INTO Quotes (customer_id, quote_date, status, total_parts, "
                "total_labour, total_amount, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (customer_id, quote_date, status, total_parts, total_labour, total_amount, notes)
            )
        else:
            # Updating an existing quote (FR06) - quote_date is left untouched
            quote_id = self.edit_quote_id
            self.db.run_update(
                "UPDATE Quotes SET customer_id=?, status=?, total_parts=?, "
                "total_labour=?, total_amount=?, notes=? WHERE quote_id=?",
                (customer_id, status, total_parts, total_labour, total_amount, notes, quote_id)
            )
            self.db.run_update("DELETE FROM QuoteLineItems WHERE quote_id = ?", (quote_id,))

        for item in parsed_items:
            self.db.run_update(
                "INSERT INTO QuoteLineItems (quote_id, description, quantity, "
                "unit_price, item_type, line_total) VALUES (?, ?, ?, ?, ?, ?)",
                (quote_id, item["description"], item["quantity"],
                 item["unit_price"], item["item_type"], item["line_total"])
            )

        self.error_label.configure(text="")
        self._show_quote_list()