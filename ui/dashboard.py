"""
ui/dashboard.py

Main app shell after login: sidebar navigation (Sketch 2) + dashboard
home screen with summary tiles and recent activity (Sketch 3).
"""

import customtkinter as ctk

COLOUR_GREEN = "#00bf63"
COLOUR_WHITE = "#ffffff"
COLOUR_ACCENT_ORANGE = "#d8ab81"
COLOUR_BLACK = "#000000"
COLOUR_BG = "#f5f5f5"
COLOUR_SIDEBAR = "#ffffff"
COLOUR_ACTIVE_ITEM = "#e6f9ee"  # light green highlight for active nav item

FONT_FAMILY = "Canva Sans"

NAV_ITEMS = ["Dashboard", "Customers", "Quotes", "Jobs", "Reports", "Settings"]


class Dashboard(ctk.CTkFrame):
    """
    App shell shown after login. Contains a header bar, a left sidebar
    for navigation, and a right content panel that swaps views.

    Pass in:
        db          - DatabaseManager instance (for querying summary data)
        username    - logged-in username, shown in header
        role        - 'Staff' or 'Admin', controls which nav items show
        on_logout   - callback run when the user clicks Logout
    """

    def __init__(self, parent, db, username, role, on_logout):
        super().__init__(parent, fg_color=COLOUR_BG)
        self.db = db
        self.username = username
        self.role = role
        self.on_logout = on_logout

        self.nav_buttons = {}
        self.active_item = "Dashboard"
        self.content_frame = None

        self.pack(fill="both", expand=True)
        self._build_header()
        self._build_body()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLOUR_WHITE, height=56, corner_radius=0)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header, text="Orbost Auto Electrics - Job Manager",
            font=(FONT_FAMILY, 16, "bold"), text_color=COLOUR_GREEN
        )
        title_label.pack(side="left", padx=20)

        user_label = ctk.CTkLabel(
            header, text=f"{self.username} ({self.role})",
            font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK
        )
        user_label.pack(side="right", padx=(0, 10))

        logout_button = ctk.CTkButton(
            header, text="Logout", width=80, height=28, corner_radius=14,
            fg_color="#e0e0e0", text_color=COLOUR_BLACK, hover_color="#cccccc",
            font=(FONT_FAMILY, 12), command=self.on_logout
        )
        logout_button.pack(side="right", padx=20)

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=COLOUR_BG, corner_radius=0)
        body.pack(side="top", fill="both", expand=True)

        self._build_sidebar(body)

        # Right content panel - views get swapped in here
        self.content_frame = ctk.CTkFrame(body, fg_color=COLOUR_BG, corner_radius=0)
        self.content_frame.pack(side="left", fill="both", expand=True)

        self._show_dashboard_home()

    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, fg_color=COLOUR_SIDEBAR, width=180, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        for item in NAV_ITEMS:
            # Admin-only nav items
            if item in ("Reports", "Settings") and self.role != "Admin":
                continue

            btn = ctk.CTkButton(
                sidebar, text=item, anchor="w",
                font=(FONT_FAMILY, 13),
                fg_color=COLOUR_ACTIVE_ITEM if item == self.active_item else "transparent",
                text_color=COLOUR_BLACK, hover_color=COLOUR_ACTIVE_ITEM,
                corner_radius=8, height=40,
                command=lambda i=item: self._on_nav_click(i)
            )
            btn.pack(fill="x", padx=12, pady=4)
            self.nav_buttons[item] = btn

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _on_nav_click(self, item):
        self.active_item = item
        for name, btn in self.nav_buttons.items():
            btn.configure(fg_color=COLOUR_ACTIVE_ITEM if name == item else "transparent")

        self._clear_content()

        if item == "Dashboard":
            self._show_dashboard_home()
        else:
            # Placeholder until each screen (Customers, Quotes, Jobs,
            # Reports, Settings) is built
            placeholder = ctk.CTkLabel(
                self.content_frame, text=f"{item} screen coming soon",
                font=(FONT_FAMILY, 16)
            )
            placeholder.pack(pady=60)

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # Dashboard home (Sketch 3)
    # ------------------------------------------------------------------

    def _show_dashboard_home(self):
        self._clear_content()
        stats = self._get_summary_stats()

        # 2x2 grid of summary tiles
        tiles_frame = ctk.CTkFrame(self.content_frame, fg_color=COLOUR_BG)
        tiles_frame.pack(fill="x", padx=30, pady=(30, 10))

        tile_data = [
            ("Total Customers", stats["total_customers"]),
            ("Open Quotes", stats["open_quotes"]),
            ("Active Jobs", stats["active_jobs"]),
            ("Completed This Month", stats["completed_this_month"]),
        ]

        for col in range(2):
            tiles_frame.grid_columnconfigure(col, weight=1)

        for index, (label_text, value) in enumerate(tile_data):
            row, col = divmod(index, 2)
            tile = ctk.CTkFrame(tiles_frame, fg_color=COLOUR_WHITE, corner_radius=12)
            tile.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            value_label = ctk.CTkLabel(
                tile, text=str(value), font=(FONT_FAMILY, 26, "bold"), text_color=COLOUR_GREEN
            )
            value_label.pack(pady=(16, 0))

            caption_label = ctk.CTkLabel(
                tile, text=label_text, font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK
            )
            caption_label.pack(pady=(0, 16))

        # Quick-add button
        quick_add = ctk.CTkButton(
            self.content_frame, text="+ New Quote", font=(FONT_FAMILY, 14, "bold"),
            fg_color=COLOUR_ACCENT_ORANGE, text_color=COLOUR_BLACK,
            corner_radius=20, height=40, width=160,
            command=lambda: self._on_nav_click("Quotes")
        )
        quick_add.pack(padx=30, pady=(10, 20), anchor="w")

        # Recent activity list
        activity_label = ctk.CTkLabel(
            self.content_frame, text="Recent Activity",
            font=(FONT_FAMILY, 14, "bold"), text_color=COLOUR_BLACK
        )
        activity_label.pack(padx=30, anchor="w")

        activity_frame = ctk.CTkFrame(self.content_frame, fg_color=COLOUR_WHITE, corner_radius=12)
        activity_frame.pack(fill="both", expand=True, padx=30, pady=(5, 30))

        recent = self._get_recent_activity()
        if not recent:
            empty_label = ctk.CTkLabel(
                activity_frame, text="No recent quotes or jobs yet",
                font=(FONT_FAMILY, 12), text_color="#888888"
            )
            empty_label.pack(pady=20)
        else:
            for entry in recent:
                row_label = ctk.CTkLabel(
                    activity_frame, text=entry, font=(FONT_FAMILY, 12),
                    text_color=COLOUR_BLACK, anchor="w"
                )
                row_label.pack(fill="x", padx=15, pady=6)

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def _get_summary_stats(self) -> dict:
        """Query the database for the four dashboard tile values."""
        total_customers = self.db.run_query("SELECT COUNT(*) FROM Customers")[0][0]

        open_quotes = self.db.run_query(
            "SELECT COUNT(*) FROM Quotes WHERE status = 'Pending'"
        )[0][0]

        active_jobs = self.db.run_query(
            "SELECT COUNT(*) FROM Jobs WHERE status IN ('Pending', 'In Progress')"
        )[0][0]

        completed_this_month = self.db.run_query(
            "SELECT COUNT(*) FROM Jobs "
            "WHERE status = 'Complete' "
            "AND strftime('%Y-%m', completion_date) = strftime('%Y-%m', 'now')"
        )[0][0]

        return {
            "total_customers": total_customers,
            "open_quotes": open_quotes,
            "active_jobs": active_jobs,
            "completed_this_month": completed_this_month,
        }

    def _get_recent_activity(self, limit: int = 5) -> list:
        """Return the most recently created quotes as simple display strings."""
        rows = self.db.run_query(
            "SELECT q.quote_id, c.customer_name, q.status, q.quote_date "
            "FROM Quotes q "
            "JOIN Customers c ON q.customer_id = c.customer_id "
            "ORDER BY q.quote_id DESC LIMIT ?",
            (limit,)
        )
        return [
            f"Quote #{quote_id} - {name} - {status} - {date}"
            for quote_id, name, status, date in rows
        ]