"""
ui/reports.py

Admin-only Profit Report screen (FR14): revenue, parts costs, labour
costs and net profit for invoiced jobs in a selected date range.
"""

import customtkinter as ctk
from datetime import datetime

COLOUR_GREEN = "#00bf63"
COLOUR_WHITE = "#ffffff"
COLOUR_RED = "#ff3131"
COLOUR_BLACK = "#000000"
COLOUR_BG = "#f5f5f5"
FONT_FAMILY = "Canva Sans"


class ReportsScreen(ctk.CTkFrame):
    """Self-contained Profit Report screen."""

    def __init__(self, parent, db):
        super().__init__(parent, fg_color=COLOUR_BG)
        self.db = db
        self.pack(fill="both", expand=True)

        self._build_layout()

    def _build_layout(self):
        title = ctk.CTkLabel(
            self, text="Profit Report", font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_BLACK
        )
        title.pack(anchor="w", padx=30, pady=(20, 15))

        # --- Date range picker ---
        range_row = ctk.CTkFrame(self, fg_color=COLOUR_BG)
        range_row.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkLabel(range_row, text="From (DD-MM-YYYY)", font=(FONT_FAMILY, 11)).pack(side="left")
        self.from_entry = ctk.CTkEntry(range_row, font=(FONT_FAMILY, 12), width=110, placeholder_text="01-01-2026")
        self.from_entry.pack(side="left", padx=(6, 20))

        ctk.CTkLabel(range_row, text="To (DD-MM-YYYY)", font=(FONT_FAMILY, 11)).pack(side="left")
        self.to_entry = ctk.CTkEntry(range_row, font=(FONT_FAMILY, 12), width=110, placeholder_text="31-12-2026")
        self.to_entry.pack(side="left", padx=(6, 20))

        generate_btn = ctk.CTkButton(
            range_row, text="Generate Report", font=(FONT_FAMILY, 12, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, corner_radius=16,
            height=32, command=self._generate_report
        )
        generate_btn.pack(side="left")

        self.error_label = ctk.CTkLabel(self, text="", font=(FONT_FAMILY, 11), text_color=COLOUR_RED)
        self.error_label.pack(anchor="w", padx=30)

        self.results_frame = ctk.CTkFrame(self, fg_color=COLOUR_BG)
        self.results_frame.pack(fill="both", expand=True, padx=30, pady=15)

        # Default to showing this month so the screen isn't empty on first load
        today = datetime.today()
        self.from_entry.insert(0, today.replace(day=1).strftime("%d-%m-%Y"))
        self.to_entry.insert(0, today.strftime("%d-%m-%Y"))
        self._generate_report()

    def _generate_report(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        self.error_label.configure(text="")

        from_str = self.from_entry.get().strip()
        to_str = self.to_entry.get().strip()

        try:
            from_date = datetime.strptime(from_str, "%d-%m-%Y")
            to_date = datetime.strptime(to_str, "%d-%m-%Y")
        except ValueError:
            self.error_label.configure(text="Enter valid dates in DD-MM-YYYY format")
            return

        if from_date > to_date:
            self.error_label.configure(text="'From' date must be before 'To' date")
            return

        # Pull invoiced jobs with a completion_date in range, joined to their
        # originating quote for the revenue/parts/labour breakdown (FR14).
        rows = self.db.run_query(
            "SELECT j.job_id, c.customer_name, j.completion_date, "
            "q.total_parts, q.total_labour, q.total_amount "
            "FROM Jobs j "
            "JOIN Customers c ON j.customer_id = c.customer_id "
            "LEFT JOIN Quotes q ON j.quote_id = q.quote_id "
            "WHERE j.status = 'Invoiced' AND j.completion_date IS NOT NULL"
        )

        matched = []
        for job_id, customer_name, completion_date, parts, labour, total in rows:
            try:
                comp_date = datetime.strptime(completion_date, "%d-%m-%Y")
            except (ValueError, TypeError):
                continue
            if from_date <= comp_date <= to_date:
                matched.append((job_id, customer_name, completion_date, parts or 0, labour or 0, total or 0))

        total_parts = sum(r[3] for r in matched)
        total_labour = sum(r[4] for r in matched)
        total_revenue = sum(r[5] for r in matched)

        # Summary tiles
        summary_row = ctk.CTkFrame(self.results_frame, fg_color=COLOUR_BG)
        summary_row.pack(fill="x", pady=(0, 15))

        tiles = [
            ("Total Revenue", total_revenue),
            ("Parts Revenue", total_parts),
            ("Labour Revenue", total_labour),
            ("Invoiced Jobs", len(matched)),
        ]
        for label_text, value in tiles:
            tile = ctk.CTkFrame(summary_row, fg_color=COLOUR_WHITE, corner_radius=12)
            tile.pack(side="left", fill="x", expand=True, padx=6)

            display_value = f"${value:.2f}" if label_text != "Invoiced Jobs" else str(value)
            ctk.CTkLabel(
                tile, text=display_value, font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_GREEN
            ).pack(pady=(14, 0))
            ctk.CTkLabel(
                tile, text=label_text, font=(FONT_FAMILY, 11), text_color=COLOUR_BLACK
            ).pack(pady=(0, 14))

        # Note on net profit, since no cost-of-goods data is tracked
        note_label = ctk.CTkLabel(
            self.results_frame,
            text="Note: this system does not track supplier cost-of-goods data, so "
                 "\"net profit\" is not distinguished from total revenue above. "
                 "Parts and Labour Revenue show the breakdown of what was charged to customers.",
            font=(FONT_FAMILY, 10), text_color="#888888", wraplength=700, justify="left"
        )
        note_label.pack(anchor="w", pady=(0, 15))

        # Detail list
        if matched:
            for job_id, customer_name, completion_date, parts, labour, total in matched:
                row_label = ctk.CTkLabel(
                    self.results_frame,
                    text=f"Job #{job_id} - {customer_name} - Completed {completion_date} - ${total:.2f}",
                    font=(FONT_FAMILY, 11), text_color=COLOUR_BLACK, anchor="w"
                )
                row_label.pack(fill="x", pady=2)
        else:
            ctk.CTkLabel(
                self.results_frame, text="No invoiced jobs found in this date range",
                font=(FONT_FAMILY, 12), text_color="#888888"
            ).pack(pady=20)