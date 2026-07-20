"""
ui/jobs.py

Jobs screen: list of active/completed jobs (FR07) with colour-coded
status, sortable/searchable columns, and a detail view for updating
job status and adding notes.
"""

import os
import tempfile
from tkinter import ttk
import customtkinter as ctk
from datetime import date, datetime

COLOUR_GREEN = "#00bf63"
COLOUR_WHITE = "#ffffff"
COLOUR_RED = "#ff3131"
COLOUR_BLACK = "#000000"
COLOUR_BG = "#f5f5f5"
FONT_FAMILY = "Canva Sans"

# Status colour coding (Design Principles & UX, Criterion 5):
# Blue = Pending, Orange = In Progress, Green = Complete, Grey = Invoiced (final)
STATUS_TAG_COLOURS = {
    "Pending": "#dbe9ff",
    "In Progress": "#ffe8cc",
    "Complete": "#d9f7e3",
    "Invoiced": "#e5e5e5",
}


class JobsScreen(ctk.CTkFrame):
    """Self-contained Jobs screen, dropped into the dashboard's content panel."""

    def __init__(self, parent, db):
        super().__init__(parent, fg_color=COLOUR_BG)
        self.db = db
        self.pack(fill="both", expand=True)

        self.body_frame = ctk.CTkFrame(self, fg_color=COLOUR_BG)
        self.body_frame.pack(fill="both", expand=True)

        self.all_job_rows = []
        self.job_rows = []
        self.sort_column = "job_id"
        self.sort_reverse = False

        self._show_job_list()

    def _clear_body(self):
        for widget in self.body_frame.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # Job list view
    # ------------------------------------------------------------------

    def _show_job_list(self):
        self._clear_body()

        header = ctk.CTkFrame(self.body_frame, fg_color=COLOUR_BG)
        header.pack(fill="x", padx=30, pady=(20, 10))

        title = ctk.CTkLabel(
            header, text="Jobs", font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_BLACK
        )
        title.pack(side="left")

        # --- Search bar (FR09) ---
        search_row = ctk.CTkFrame(self.body_frame, fg_color=COLOUR_BG)
        search_row.pack(fill="x", padx=30, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_row, placeholder_text="Search by customer, vehicle, job ID or status",
            font=(FONT_FAMILY, 12), width=360
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_jobs())

        self.result_label = ctk.CTkLabel(
            search_row, text="", font=(FONT_FAMILY, 11), text_color="#888888"
        )
        self.result_label.pack(side="left", padx=(10, 0))

        # --- Treeview ---
        style = ttk.Style()
        style.configure("Jobs.Treeview", font=(FONT_FAMILY, 11), rowheight=28)
        style.configure("Jobs.Treeview.Heading", font=(FONT_FAMILY, 11, "bold"))

        columns = ("job_id", "customer", "quote_ref", "status", "job_date", "completion_date")
        self.job_tree = ttk.Treeview(
            self.body_frame, columns=columns, show="headings",
            style="Jobs.Treeview", height=15
        )

        heading_labels = {
            "job_id": "Job ID", "customer": "Customer", "quote_ref": "From Quote",
            "status": "Status", "job_date": "Job Date", "completion_date": "Completed"
        }
        for col, label in heading_labels.items():
            self.job_tree.heading(col, text=label, command=lambda c=col: self._sort_jobs(c))

        self.job_tree.column("job_id", width=70, anchor="center")
        self.job_tree.column("customer", width=170)
        self.job_tree.column("quote_ref", width=90, anchor="center")
        self.job_tree.column("status", width=110, anchor="center")
        self.job_tree.column("job_date", width=110, anchor="center")
        self.job_tree.column("completion_date", width=110, anchor="center")

        for status, colour in STATUS_TAG_COLOURS.items():
            self.job_tree.tag_configure(status, background=colour)

        self.job_tree.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        self.job_tree.bind("<Double-1>", self._on_job_row_double_click)

        hint_label = ctk.CTkLabel(
            self.body_frame, text="Double-click a job to update its status or add notes",
            font=(FONT_FAMILY, 10), text_color="#888888"
        )
        hint_label.pack(padx=30, pady=(0, 10), anchor="w")

        self.all_job_rows = self.db.run_query(
            "SELECT j.job_id, c.customer_name, j.quote_id, j.status, j.job_date, "
            "j.completion_date, c.vehicle_make, c.vehicle_model, c.vehicle_rego "
            "FROM Jobs j JOIN Customers c ON j.customer_id = c.customer_id"
        )
        self.job_rows = list(self.all_job_rows)
        self._apply_sort()
        self._populate_job_tree()

    def _populate_job_tree(self):
        self.job_tree.delete(*self.job_tree.get_children())
        for row in self.job_rows:
            job_id, name, quote_id, status, job_date, completion_date = row[0], row[1], row[2], row[3], row[4], row[5]
            quote_ref = f"#{quote_id}" if quote_id else "-"
            completed_display = completion_date if completion_date else "-"
            self.job_tree.insert(
                "", "end",
                values=(job_id, name, quote_ref, status, job_date, completed_display),
                tags=(status,)
            )
        self._update_sort_indicators()

    def _apply_sort(self):
        col_index = {
            "job_id": 0, "customer": 1, "quote_ref": 2,
            "status": 3, "job_date": 4, "completion_date": 5
        }[self.sort_column]

        def sort_key(row):
            value = row[col_index]
            if self.sort_column in ("job_date", "completion_date"):
                if not value:
                    return datetime.min
                try:
                    return datetime.strptime(value, "%d-%m-%Y")
                except (ValueError, TypeError):
                    return datetime.min
            if self.sort_column in ("customer", "status"):
                return str(value).lower()
            if self.sort_column == "quote_ref":
                return value or 0
            return value

        self.job_rows = sorted(self.job_rows, key=sort_key, reverse=self.sort_reverse)

    def _sort_jobs(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            # Dates default to newest-first; everything else ascending
            self.sort_reverse = column in ("job_date", "completion_date")

        self._apply_sort()
        self._populate_job_tree()

    def _update_sort_indicators(self):
        heading_labels = {
            "job_id": "Job ID", "customer": "Customer", "quote_ref": "From Quote",
            "status": "Status", "job_date": "Job Date", "completion_date": "Completed"
        }
        for col, label in heading_labels.items():
            if col == self.sort_column:
                arrow = " ▼" if self.sort_reverse else " ▲"
                self.job_tree.heading(col, text=label + arrow)
            else:
                self.job_tree.heading(col, text=label)

    def _filter_jobs(self):
        term = self.search_entry.get().strip().lower()
        if not term:
            self.job_rows = list(self.all_job_rows)
        else:
            def matches(row):
                job_id, name, quote_id, status, job_date, completion_date, make, model, rego = row
                haystack = f"{job_id} {name} {status} {make} {model} {rego}".lower()
                return term in haystack
            self.job_rows = [r for r in self.all_job_rows if matches(r)]

        self._apply_sort()
        self._populate_job_tree()

        if term and not self.job_rows:
            self.result_label.configure(text="No results found")
        elif term:
            self.result_label.configure(text=f"{len(self.job_rows)} result(s)")
        else:
            self.result_label.configure(text="")

    def _on_job_row_double_click(self, event):
        selection = self.job_tree.selection()
        if not selection:
            return
        values = self.job_tree.item(selection[0], "values")
        job_id = int(values[0])
        self._show_job_detail(job_id)

    # ------------------------------------------------------------------
    # Job detail / edit view (FR07: update status, add notes)
    # ------------------------------------------------------------------

    def _show_job_detail(self, job_id):
        self._clear_body()

        row = self.db.run_query(
            "SELECT j.job_id, c.customer_name, j.quote_id, j.status, j.job_date, "
            "j.completion_date, j.notes "
            "FROM Jobs j JOIN Customers c ON j.customer_id = c.customer_id "
            "WHERE j.job_id = ?",
            (job_id,)
        )
        if not row:
            self._show_job_list()
            return
        _, customer_name, quote_id, status, job_date, completion_date, notes = row[0]

        container = ctk.CTkFrame(self.body_frame, fg_color=COLOUR_BG)
        container.pack(fill="both", expand=True, padx=30, pady=20)

        title = ctk.CTkLabel(
            container, text=f"Job #{job_id} - {customer_name}",
            font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_BLACK
        )
        title.pack(anchor="w", pady=(0, 5))

        meta_text = f"Job Date: {job_date}"
        if quote_id:
            meta_text += f"   |   From Quote #{quote_id}"
        if completion_date:
            meta_text += f"   |   Completed: {completion_date}"
        meta_label = ctk.CTkLabel(
            container, text=meta_text, font=(FONT_FAMILY, 11), text_color="#666666"
        )
        meta_label.pack(anchor="w", pady=(0, 20))

        # --- Status ---
        ctk.CTkLabel(
            container, text="Status", font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK
        ).pack(anchor="w")

        is_invoiced = (status == "Invoiced")
        status_values = ["Pending", "In Progress", "Complete"]
        if is_invoiced:
            status_values.append("Invoiced")

        status_combo = ctk.CTkComboBox(
            container, values=status_values,
            font=(FONT_FAMILY, 12), width=200,
            state="disabled" if is_invoiced else "normal"
        )
        status_combo.set(status)
        status_combo.pack(anchor="w", pady=(4, 15))

        # --- Notes ---
        ctk.CTkLabel(
            container, text="Job Notes", font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK
        ).pack(anchor="w")
        notes_box = ctk.CTkTextbox(container, height=120, font=(FONT_FAMILY, 12))
        notes_box.pack(fill="x", pady=(4, 15))
        if notes:
            notes_box.insert("1.0", notes)
        if is_invoiced:
            notes_box.configure(state="disabled")

        error_label = ctk.CTkLabel(container, text="", font=(FONT_FAMILY, 11), text_color=COLOUR_RED)
        error_label.pack(anchor="w")

        # --- Buttons ---
        button_row = ctk.CTkFrame(container, fg_color=COLOUR_BG)
        button_row.pack(fill="x", pady=(15, 0))

        cancel_btn = ctk.CTkButton(
            button_row, text="Back to Jobs List", font=(FONT_FAMILY, 13),
            fg_color="#e0e0e0", text_color=COLOUR_BLACK, hover_color="#cccccc",
            corner_radius=18, height=36, width=140,
            command=self._show_job_list
        )
        cancel_btn.pack(side="left")

        if is_invoiced:
            # Final state: only viewing the invoice makes sense now
            view_invoice_btn = ctk.CTkButton(
                button_row, text="View Invoice", font=(FONT_FAMILY, 13, "bold"),
                fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK,
                corner_radius=18, height=36, width=140,
                command=lambda: self._show_invoice(job_id)
            )
            view_invoice_btn.pack(side="right")
            return

        def save_changes():
            new_status = status_combo.get()
            new_notes = notes_box.get("1.0", "end").strip() or None
            new_completion_date = completion_date

            if new_status == "Complete" and not completion_date:
                new_completion_date = date.today().strftime("%d-%m-%Y")

            self.db.run_update(
                "UPDATE Jobs SET status=?, notes=?, completion_date=? WHERE job_id=?",
                (new_status, new_notes, new_completion_date, job_id)
            )
            self._show_job_list()

        save_btn = ctk.CTkButton(
            button_row, text="Save Changes", font=(FONT_FAMILY, 13, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK,
            corner_radius=18, height=36, width=140,
            command=save_changes
        )
        save_btn.pack(side="right")

        # Convert to Invoice (FR08) - only available once the job is Complete
        if status == "Complete":
            def convert_to_invoice():
                self.db.run_update(
                    "UPDATE Jobs SET status='Invoiced' WHERE job_id=?", (job_id,)
                )
                self._show_invoice(job_id)

            invoice_btn = ctk.CTkButton(
                button_row, text="Convert to Invoice", font=(FONT_FAMILY, 13, "bold"),
                fg_color="#d8ab81", text_color=COLOUR_BLACK,
                corner_radius=18, height=36, width=160,
                command=convert_to_invoice
            )
            invoice_btn.pack(side="right", padx=(0, 10))

    # ------------------------------------------------------------------
    # Formatted invoice display (FR08) - on-screen, printable
    # ------------------------------------------------------------------

    def _show_invoice(self, job_id):
        self._clear_body()

        job_row = self.db.run_query(
            "SELECT j.job_id, j.quote_id, j.job_date, j.completion_date, "
            "c.customer_name, c.phone, c.email, c.vehicle_make, c.vehicle_model, "
            "c.vehicle_year, c.vehicle_rego "
            "FROM Jobs j JOIN Customers c ON j.customer_id = c.customer_id "
            "WHERE j.job_id = ?",
            (job_id,)
        )
        if not job_row:
            self._show_job_list()
            return
        (job_id, quote_id, job_date, completion_date, customer_name, phone,
         email, make, model, year, rego) = job_row[0]

        line_items = []
        total_parts = total_labour = total_amount = 0.0
        if quote_id:
            quote_row = self.db.run_query(
                "SELECT total_parts, total_labour, total_amount FROM Quotes WHERE quote_id = ?",
                (quote_id,)
            )
            if quote_row:
                total_parts, total_labour, total_amount = quote_row[0]
            line_items = self.db.run_query(
                "SELECT description, quantity, unit_price, item_type, line_total "
                "FROM QuoteLineItems WHERE quote_id = ?",
                (quote_id,)
            )

        # Scrollable invoice container styled like a printable document
        outer = ctk.CTkScrollableFrame(self.body_frame, fg_color=COLOUR_BG)
        outer.pack(fill="both", expand=True, padx=30, pady=20)

        sheet = ctk.CTkFrame(outer, fg_color=COLOUR_WHITE, corner_radius=10)
        sheet.pack(fill="x", pady=10)

        header = ctk.CTkLabel(
            sheet, text="Orbost Auto Electrics", font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_GREEN
        )
        header.pack(anchor="w", padx=30, pady=(25, 0))

        subheader = ctk.CTkLabel(
            sheet, text="Tax Invoice", font=(FONT_FAMILY, 14), text_color=COLOUR_BLACK
        )
        subheader.pack(anchor="w", padx=30, pady=(0, 15))

        details_text = (
            f"Invoice for Job #{job_id}" + (f"  (from Quote #{quote_id})" if quote_id else "") + "\n"
            f"Job Date: {job_date}     Completed: {completion_date or '-'}\n\n"
            f"Customer: {customer_name}\n"
            f"Phone: {phone}" + (f"   Email: {email}" if email else "") + "\n"
            f"Vehicle: {year} {make} {model} - Rego: {rego}"
        )
        details_label = ctk.CTkLabel(
            sheet, text=details_text, font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK, justify="left"
        )
        details_label.pack(anchor="w", padx=30, pady=(0, 20))

        # Line items table
        table_frame = ctk.CTkFrame(sheet, fg_color=COLOUR_BG, corner_radius=8)
        table_frame.pack(fill="x", padx=30, pady=(0, 15))

        col_headers = ["Description", "Qty", "Unit Price", "Type", "Line Total"]
        header_row = ctk.CTkFrame(table_frame, fg_color=COLOUR_BG)
        header_row.pack(fill="x", padx=10, pady=(8, 4))
        widths = [260, 60, 100, 90, 100]
        for h, w in zip(col_headers, widths):
            ctk.CTkLabel(
                header_row, text=h, font=(FONT_FAMILY, 11, "bold"), text_color=COLOUR_BLACK,
                width=w, anchor="w"
            ).pack(side="left")

        for description, quantity, unit_price, item_type, line_total in line_items:
            row = ctk.CTkFrame(table_frame, fg_color=COLOUR_BG)
            row.pack(fill="x", padx=10, pady=2)
            values = [description, f"{quantity:g}", f"${unit_price:.2f}", item_type, f"${line_total:.2f}"]
            for v, w in zip(values, widths):
                ctk.CTkLabel(
                    row, text=v, font=(FONT_FAMILY, 11), text_color=COLOUR_BLACK,
                    width=w, anchor="w"
                ).pack(side="left")

        if not line_items:
            ctk.CTkLabel(
                table_frame, text="No line items found (job was not linked to a quote)",
                font=(FONT_FAMILY, 11), text_color="#888888"
            ).pack(padx=10, pady=10)

        # Totals
        totals_text = (
            f"Parts: ${total_parts:.2f}     Labour: ${total_labour:.2f}\n"
            f"Total: ${total_amount:.2f}"
        )
        totals_label = ctk.CTkLabel(
            sheet, text=totals_text, font=(FONT_FAMILY, 14, "bold"), text_color=COLOUR_GREEN, justify="right"
        )
        totals_label.pack(anchor="e", padx=30, pady=(0, 25))

        # Buttons
        button_row = ctk.CTkFrame(outer, fg_color=COLOUR_BG)
        button_row.pack(fill="x", pady=(0, 10))

        back_btn = ctk.CTkButton(
            button_row, text="Back to Jobs List", font=(FONT_FAMILY, 13),
            fg_color="#e0e0e0", text_color=COLOUR_BLACK, hover_color="#cccccc",
            corner_radius=18, height=36, width=140,
            command=self._show_job_list
        )
        back_btn.pack(side="left")

        print_status_label = ctk.CTkLabel(button_row, text="", font=(FONT_FAMILY, 10), text_color="#888888")
        print_status_label.pack(side="left", padx=(10, 0))

        def print_invoice():
            self._print_invoice_text(
                job_id, quote_id, job_date, completion_date, customer_name, phone,
                email, make, model, year, rego, line_items,
                total_parts, total_labour, total_amount, print_status_label
            )

        print_btn = ctk.CTkButton(
            button_row, text="Print", font=(FONT_FAMILY, 13, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK,
            corner_radius=18, height=36, width=100,
            command=print_invoice
        )
        print_btn.pack(side="right")

    def _print_invoice_text(self, job_id, quote_id, job_date, completion_date, customer_name,
                             phone, email, make, model, year, rego, line_items,
                             total_parts, total_labour, total_amount, status_label):
        """Write the invoice to a temp text file and send it to the OS print
        function. Falls back to just saving the file if printing isn't
        available (e.g. non-Windows or no default printer configured)."""
        lines = []
        lines.append("ORBOST AUTO ELECTRICS - TAX INVOICE")
        lines.append("=" * 40)
        lines.append(f"Job #{job_id}" + (f" (from Quote #{quote_id})" if quote_id else ""))
        lines.append(f"Job Date: {job_date}   Completed: {completion_date or '-'}")
        lines.append("")
        lines.append(f"Customer: {customer_name}")
        lines.append(f"Phone: {phone}" + (f"   Email: {email}" if email else ""))
        lines.append(f"Vehicle: {year} {make} {model} - Rego: {rego}")
        lines.append("")
        lines.append(f"{'Description':<30}{'Qty':<8}{'Unit Price':<12}{'Type':<10}{'Line Total':<10}")
        lines.append("-" * 70)
        for description, quantity, unit_price, item_type, line_total in line_items:
            lines.append(
                f"{description:<30}{quantity:<8g}${unit_price:<11.2f}{item_type:<10}${line_total:<9.2f}"
            )
        lines.append("-" * 70)
        lines.append(f"Parts: ${total_parts:.2f}   Labour: ${total_labour:.2f}")
        lines.append(f"TOTAL: ${total_amount:.2f}")

        content = "\n".join(lines)

        try:
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"invoice_job_{job_id}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            if os.name == "nt":
                os.startfile(file_path, "print")
                status_label.configure(text="Sent to printer")
            else:
                status_label.configure(text=f"Saved to {file_path} (auto-print not supported on this OS)")
        except Exception:
            status_label.configure(text="Could not print - check your default printer is set up")