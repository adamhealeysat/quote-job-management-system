"""
ui/customers.py

Customers screen: list with search (IPO 4), add/edit customer, and
delete with a safeguard against orphaning linked quotes/jobs
(Possible Errors table, Criterion 5).
"""

import customtkinter as ctk
from tkinter import ttk

from ui.validators import validate_customer_fields

COLOUR_GREEN = "#00bf63"
COLOUR_WHITE = "#ffffff"
COLOUR_RED = "#ff3131"
COLOUR_BLACK = "#000000"
COLOUR_BG = "#f5f5f5"
FONT_FAMILY = "Canva Sans"


class CustomersScreen(ctk.CTkFrame):
    """Self-contained Customers screen, dropped into the dashboard's content panel."""

    def __init__(self, parent, db):
        super().__init__(parent, fg_color=COLOUR_BG)
        self.db = db
        self.pack(fill="both", expand=True)

        self.selected_customer_id = None
        self._show_list()

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # List view (FR09 search, sort not required here but list is sortable
    # via the same Treeview heading pattern if extended later)
    # ------------------------------------------------------------------

    def _show_list(self):
        self._clear()
        self.selected_customer_id = None

        header = ctk.CTkFrame(self, fg_color=COLOUR_BG)
        header.pack(fill="x", padx=30, pady=(20, 10))

        title = ctk.CTkLabel(
            header, text="Customers", font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_BLACK
        )
        title.pack(side="left")

        add_btn = ctk.CTkButton(
            header, text="+ Add Customer", font=(FONT_FAMILY, 13, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, corner_radius=18,
            height=34, command=lambda: self._open_customer_dialog()
        )
        add_btn.pack(side="right")

        # --- Search bar (IPO 4: name, phone or vehicle rego) ---
        search_row = ctk.CTkFrame(self, fg_color=COLOUR_BG)
        search_row.pack(fill="x", padx=30, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_row, placeholder_text="Search by name, phone or rego",
            font=(FONT_FAMILY, 12), width=320
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_tree())

        self.result_count_label = ctk.CTkLabel(
            search_row, text="", font=(FONT_FAMILY, 11), text_color="#888888"
        )
        self.result_count_label.pack(side="left", padx=(10, 0))

        # --- Treeview ---
        style = ttk.Style()
        style.configure("Customers.Treeview", font=(FONT_FAMILY, 11), rowheight=28)
        style.configure("Customers.Treeview.Heading", font=(FONT_FAMILY, 11, "bold"))

        columns = ("id", "name", "phone", "vehicle", "rego")
        self.tree = ttk.Treeview(
            self, columns=columns, show="headings", style="Customers.Treeview", height=14
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("vehicle", text="Vehicle")
        self.tree.heading("rego", text="Rego")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=180)
        self.tree.column("phone", width=120)
        self.tree.column("vehicle", width=200)
        self.tree.column("rego", width=100, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)
        self.tree.bind("<Double-1>", lambda e: self._open_customer_dialog(self.selected_customer_id))

        # --- Action buttons (enabled once a row is selected) ---
        action_row = ctk.CTkFrame(self, fg_color=COLOUR_BG)
        action_row.pack(fill="x", padx=30, pady=(0, 20))

        self.edit_btn = ctk.CTkButton(
            action_row, text="Edit", font=(FONT_FAMILY, 12), width=90, height=32,
            corner_radius=16, fg_color="#e0e0e0", text_color=COLOUR_BLACK,
            hover_color="#cccccc", state="disabled",
            command=lambda: self._open_customer_dialog(self.selected_customer_id)
        )
        self.edit_btn.pack(side="left", padx=(0, 8))

        self.delete_btn = ctk.CTkButton(
            action_row, text="Delete", font=(FONT_FAMILY, 12), width=90, height=32,
            corner_radius=16, fg_color=COLOUR_RED, text_color=COLOUR_WHITE,
            hover_color="#cc2020", state="disabled",
            command=self._delete_selected_customer
        )
        self.delete_btn.pack(side="left")

        self._refresh_tree()

    def _on_row_select(self, event):
        selection = self.tree.selection()
        if not selection:
            self.selected_customer_id = None
            self.edit_btn.configure(state="disabled")
            self.delete_btn.configure(state="disabled")
            return
        values = self.tree.item(selection[0], "values")
        self.selected_customer_id = int(values[0])
        self.edit_btn.configure(state="normal")
        self.delete_btn.configure(state="normal")

    def _refresh_tree(self):
        """Reload customers from the database, applying the search term (IPO 4)."""
        term = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""

        if term:
            like = f"%{term}%"
            rows = self.db.run_query(
                "SELECT customer_id, customer_name, phone, vehicle_make, vehicle_model, vehicle_rego "
                "FROM Customers WHERE customer_name LIKE ? OR phone LIKE ? OR vehicle_rego LIKE ? "
                "ORDER BY customer_name",
                (like, like, like)
            )
        else:
            rows = self.db.run_query(
                "SELECT customer_id, customer_name, phone, vehicle_make, vehicle_model, vehicle_rego "
                "FROM Customers ORDER BY customer_name"
            )

        self.tree.delete(*self.tree.get_children())
        for customer_id, name, phone, make, model, rego in rows:
            vehicle = f"{make} {model}"
            self.tree.insert("", "end", values=(customer_id, name, phone, vehicle, rego))

        if term and not rows:
            self.result_count_label.configure(text="No results found")
        elif term:
            self.result_count_label.configure(text=f"{len(rows)} result(s)")
        else:
            self.result_count_label.configure(text=f"{len(rows)} customer(s)")

    # ------------------------------------------------------------------
    # Add / Edit dialog
    # ------------------------------------------------------------------

    def _open_customer_dialog(self, customer_id=None):
        is_edit = customer_id is not None

        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Customer" if is_edit else "Add New Customer")
        dialog.geometry("380x520")
        dialog.grab_set()

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

        existing = None
        if is_edit:
            rows = self.db.run_query(
                "SELECT customer_name, phone, email, vehicle_make, vehicle_model, "
                "vehicle_year, vehicle_rego FROM Customers WHERE customer_id = ?",
                (customer_id,)
            )
            if rows:
                existing = rows[0]

        for index, (key, label_text) in enumerate(field_specs):
            ctk.CTkLabel(scroll_frame, text=label_text, font=(FONT_FAMILY, 11)).pack(anchor="w", pady=(8, 0))
            entry = ctk.CTkEntry(scroll_frame, font=(FONT_FAMILY, 11), width=300)
            entry.pack()
            if existing is not None:
                value = existing[index]
                if value is not None:
                    entry.insert(0, str(value))
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

            is_valid, message = validate_customer_fields(
                name, phone, email, make, model, year_str, rego
            )
            if not is_valid:
                error_label.configure(text=message)
                return

            year = int(year_str)

            if is_edit:
                self.db.run_update(
                    "UPDATE Customers SET customer_name=?, phone=?, email=?, vehicle_make=?, "
                    "vehicle_model=?, vehicle_year=?, vehicle_rego=? WHERE customer_id=?",
                    (name, phone, email, make, model, year, rego, customer_id)
                )
            else:
                self.db.run_update(
                    "INSERT INTO Customers (customer_name, phone, email, vehicle_make, "
                    "vehicle_model, vehicle_year, vehicle_rego) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (name, phone, email, make, model, year, rego)
                )

            dialog.destroy()
            self._refresh_tree()

        save_btn = ctk.CTkButton(
            dialog, text="Save Changes" if is_edit else "Save Customer",
            font=(FONT_FAMILY, 12, "bold"), fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK,
            corner_radius=16, height=36, command=save_customer
        )
        save_btn.pack(pady=(0, 15))

    # ------------------------------------------------------------------
    # Delete with linked-record safeguard
    # (Criterion 5, Possible Errors: check for linked quotes/jobs before
    # deleting; warn and require explicit confirmation to cascade-delete.)
    # ------------------------------------------------------------------

    def _delete_selected_customer(self):
        if self.selected_customer_id is None:
            return
        customer_id = self.selected_customer_id

        quote_count = self.db.run_query(
            "SELECT COUNT(*) FROM Quotes WHERE customer_id = ?", (customer_id,)
        )[0][0]
        job_count = self.db.run_query(
            "SELECT COUNT(*) FROM Jobs WHERE customer_id = ?", (customer_id,)
        )[0][0]

        if quote_count == 0 and job_count == 0:
            self._show_confirm_dialog(
                "Delete Customer",
                "Are you sure you want to delete this customer? This cannot be undone.",
                lambda: self._perform_delete(customer_id, cascade=False)
            )
        else:
            message = (
                f"This customer has {quote_count} quote(s) and {job_count} job(s) linked to them.\n\n"
                "Deleting this customer will also permanently delete all of their linked "
                "quotes and jobs. This cannot be undone.\n\n"
                "Do you want to continue?"
            )
            self._show_confirm_dialog(
                "Linked Records Found",
                message,
                lambda: self._perform_delete(customer_id, cascade=True)
            )

    def _perform_delete(self, customer_id, cascade):
        if cascade:
            quote_ids = [
                row[0] for row in self.db.run_query(
                    "SELECT quote_id FROM Quotes WHERE customer_id = ?", (customer_id,)
                )
            ]
            for quote_id in quote_ids:
                self.db.run_update("DELETE FROM QuoteLineItems WHERE quote_id = ?", (quote_id,))
            self.db.run_update("DELETE FROM Quotes WHERE customer_id = ?", (customer_id,))
            self.db.run_update("DELETE FROM Jobs WHERE customer_id = ?", (customer_id,))

        self.db.run_update("DELETE FROM Customers WHERE customer_id = ?", (customer_id,))
        self._show_list()

    def _show_confirm_dialog(self, title, message, on_confirm):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("380x260")
        dialog.grab_set()

        label = ctk.CTkLabel(
            dialog, text=message, font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK,
            wraplength=330, justify="left"
        )
        label.pack(padx=20, pady=20, fill="both", expand=True)

        button_row = ctk.CTkFrame(dialog, fg_color=COLOUR_BG)
        button_row.pack(pady=(0, 15))

        def confirm_and_close():
            dialog.destroy()
            on_confirm()

        cancel_btn = ctk.CTkButton(
            button_row, text="Cancel", font=(FONT_FAMILY, 12), width=100, height=34,
            corner_radius=16, fg_color="#e0e0e0", text_color=COLOUR_BLACK,
            hover_color="#cccccc", command=dialog.destroy
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        confirm_btn = ctk.CTkButton(
            button_row, text="Delete", font=(FONT_FAMILY, 12, "bold"), width=100, height=34,
            corner_radius=16, fg_color=COLOUR_RED, text_color=COLOUR_WHITE,
            hover_color="#cc2020", command=confirm_and_close
        )
        confirm_btn.pack(side="left")