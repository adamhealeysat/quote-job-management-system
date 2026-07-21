"""
ui/settings.py - Quote & Job Management System

Admin-only Settings screen: manage the parts catalogue and labour rate
(FR11, FR12) and manage staff/admin user accounts including password
reset (FR13, Criterion 5 Undefined scope addition).

@author ***Adam Healey***
"""

import customtkinter as ctk
from tkinter import ttk, filedialog
from datetime import datetime

from ui.validators import (
    validate_part_name,
    validate_currency_amount,
    validate_username,
    validate_password,
)

COLOUR_GREEN = "#00bf63"
COLOUR_WHITE = "#ffffff"
COLOUR_RED = "#ff3131"
COLOUR_BLACK = "#000000"
COLOUR_BG = "#f5f5f5"
FONT_FAMILY = "Canva Sans"

TABS = ["Parts Catalogue", "Labour Rate", "User Accounts", "Backup & Export"]


class SettingsScreen(ctk.CTkFrame):
    """Self-contained Admin Settings screen with three sub-tabs."""

    def __init__(self, parent, db, auth):
        super().__init__(parent, fg_color=COLOUR_BG)
        self.db = db
        self.auth = auth
        self.pack(fill="both", expand=True)

        self.active_tab = "Parts Catalogue"
        self.content_frame = None

        self._build_layout()

    def _build_layout(self):
        title = ctk.CTkLabel(
            self, text="Settings", font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_BLACK
        )
        title.pack(anchor="w", padx=30, pady=(20, 10))

        tab_row = ctk.CTkFrame(self, fg_color=COLOUR_BG)
        tab_row.pack(fill="x", padx=30)

        self.tab_buttons = {}
        for tab in TABS:
            btn = ctk.CTkButton(
                tab_row, text=tab, font=(FONT_FAMILY, 12, "bold"),
                fg_color=COLOUR_GREEN if tab == self.active_tab else "#e0e0e0",
                text_color=COLOUR_BLACK if tab == self.active_tab else COLOUR_BLACK,
                hover_color="#00a855", corner_radius=16, height=32,
                command=lambda t=tab: self._switch_tab(t)
            )
            btn.pack(side="left", padx=(0, 8))
            self.tab_buttons[tab] = btn

        self.content_frame = ctk.CTkFrame(self, fg_color=COLOUR_BG)
        self.content_frame.pack(fill="both", expand=True, padx=30, pady=15)

        self._render_active_tab()

    def _switch_tab(self, tab):
        self.active_tab = tab
        for name, btn in self.tab_buttons.items():
            btn.configure(fg_color=COLOUR_GREEN if name == tab else "#e0e0e0")
        self._render_active_tab()

    def _render_active_tab(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if self.active_tab == "Parts Catalogue":
            self._render_parts_tab()
        elif self.active_tab == "Labour Rate":
            self._render_labour_rate_tab()
        elif self.active_tab == "User Accounts":
            self._render_users_tab()
        elif self.active_tab == "Backup & Export":
            self._render_backup_tab()

    # ------------------------------------------------------------------
    # Parts Catalogue (FR11)
    # ------------------------------------------------------------------

    def _render_parts_tab(self):
        add_row = ctk.CTkFrame(self.content_frame, fg_color=COLOUR_BG)
        add_row.pack(fill="x", pady=(0, 10))

        name_entry = ctk.CTkEntry(add_row, placeholder_text="Part name", font=(FONT_FAMILY, 12), width=220)
        name_entry.pack(side="left", padx=(0, 8))

        cost_entry = ctk.CTkEntry(add_row, placeholder_text="Unit cost", font=(FONT_FAMILY, 12), width=100)
        cost_entry.pack(side="left", padx=(0, 8))

        error_label = ctk.CTkLabel(self.content_frame, text="", font=(FONT_FAMILY, 11), text_color=COLOUR_RED)

        def add_part():
            name = name_entry.get().strip()
            cost_str = cost_entry.get().strip()

            is_valid, message = validate_part_name(name)
            if not is_valid:
                error_label.configure(text=message)
                error_label.pack(anchor="w", pady=(0, 5))
                return

            is_valid, message = validate_currency_amount(cost_str, "Unit cost")
            if not is_valid:
                error_label.configure(text=message)
                error_label.pack(anchor="w", pady=(0, 5))
                return

            cost = float(cost_str)

            self.db.run_update(
                "INSERT INTO PartsCatalogue (part_name, unit_cost, is_active) VALUES (?, ?, 1)",
                (name, cost)
            )
            error_label.configure(text="")
            self._render_parts_tab()

        add_btn = ctk.CTkButton(
            add_row, text="+ Add Part", font=(FONT_FAMILY, 12, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, corner_radius=16,
            height=32, width=110, command=add_part
        )
        add_btn.pack(side="left")

        style = ttk.Style()
        style.configure("Parts.Treeview", font=(FONT_FAMILY, 11), rowheight=28)
        style.configure("Parts.Treeview.Heading", font=(FONT_FAMILY, 11, "bold"))

        columns = ("id", "name", "cost", "status")
        tree = ttk.Treeview(self.content_frame, columns=columns, show="headings", style="Parts.Treeview", height=12)
        tree.heading("id", text="ID")
        tree.heading("name", text="Part Name")
        tree.heading("cost", text="Unit Cost")
        tree.heading("status", text="Status")
        tree.column("id", width=50, anchor="center")
        tree.column("name", width=250)
        tree.column("cost", width=100, anchor="e")
        tree.column("status", width=100, anchor="center")
        tree.pack(fill="both", expand=True, pady=(0, 10))

        rows = self.db.run_query("SELECT part_id, part_name, unit_cost, is_active FROM PartsCatalogue ORDER BY part_name")
        for part_id, name, cost, is_active in rows:
            tree.insert("", "end", values=(part_id, name, f"${cost:.2f}", "Active" if is_active else "Deactivated"))

        action_row = ctk.CTkFrame(self.content_frame, fg_color=COLOUR_BG)
        action_row.pack(fill="x")

        def get_selected_part_id():
            sel = tree.selection()
            if not sel:
                return None
            return int(tree.item(sel[0], "values")[0])

        def toggle_active():
            part_id = get_selected_part_id()
            if part_id is None:
                return
            current = self.db.run_query("SELECT is_active FROM PartsCatalogue WHERE part_id=?", (part_id,))[0][0]
            self.db.run_update(
                "UPDATE PartsCatalogue SET is_active=? WHERE part_id=?", (0 if current else 1, part_id)
            )
            self._render_parts_tab()

        toggle_btn = ctk.CTkButton(
            action_row, text="Activate / Deactivate", font=(FONT_FAMILY, 12),
            fg_color="#e0e0e0", text_color=COLOUR_BLACK, hover_color="#cccccc",
            corner_radius=16, height=32, command=toggle_active
        )
        toggle_btn.pack(side="left")

    # ------------------------------------------------------------------
    # Labour Rate (FR12)
    # ------------------------------------------------------------------

    def _render_labour_rate_tab(self):
        current_rate = self.db.run_query(
            "SELECT setting_value FROM Settings WHERE setting_key='labour_rate'"
        )[0][0]

        info_label = ctk.CTkLabel(
            self.content_frame,
            text=f"Current hourly labour rate: ${float(current_rate):.2f}",
            font=(FONT_FAMILY, 16, "bold"), text_color=COLOUR_GREEN
        )
        info_label.pack(anchor="w", pady=(0, 15))

        note_label = ctk.CTkLabel(
            self.content_frame,
            text="Changing this rate only affects new quotes going forward.\n"
                 "Existing saved quotes are not recalculated (FR12).",
            font=(FONT_FAMILY, 11), text_color="#888888", justify="left"
        )
        note_label.pack(anchor="w", pady=(0, 15))

        update_row = ctk.CTkFrame(self.content_frame, fg_color=COLOUR_BG)
        update_row.pack(fill="x")

        rate_entry = ctk.CTkEntry(update_row, placeholder_text="New rate", font=(FONT_FAMILY, 12), width=120)
        rate_entry.pack(side="left", padx=(0, 8))

        error_label = ctk.CTkLabel(self.content_frame, text="", font=(FONT_FAMILY, 11), text_color=COLOUR_RED)

        def update_rate():
            rate_str = rate_entry.get().strip()

            is_valid, message = validate_currency_amount(rate_str, "Labour rate")
            if not is_valid:
                error_label.configure(text=message)
                error_label.pack(anchor="w", pady=(8, 0))
                return

            rate = float(rate_str)
            self.db.run_update(
                "UPDATE Settings SET setting_value=? WHERE setting_key='labour_rate'",
                (f"{rate:.2f}",)
            )
            self._render_labour_rate_tab()

        update_btn = ctk.CTkButton(
            update_row, text="Update Rate", font=(FONT_FAMILY, 12, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, corner_radius=16,
            height=32, width=120, command=update_rate
        )
        update_btn.pack(side="left")

    # ------------------------------------------------------------------
    # User Accounts (FR13 + password reset scope addition)
    # ------------------------------------------------------------------

    def _render_users_tab(self):
        add_row = ctk.CTkFrame(self.content_frame, fg_color=COLOUR_BG)
        add_row.pack(fill="x", pady=(0, 10))

        username_entry = ctk.CTkEntry(add_row, placeholder_text="Username", font=(FONT_FAMILY, 12), width=140)
        username_entry.pack(side="left", padx=(0, 8))

        password_entry = ctk.CTkEntry(add_row, placeholder_text="Temp password", show="*", font=(FONT_FAMILY, 12), width=140)
        password_entry.pack(side="left", padx=(0, 8))

        role_combo = ctk.CTkComboBox(add_row, values=["Staff", "Admin"], font=(FONT_FAMILY, 12), width=100)
        role_combo.set("Staff")
        role_combo.pack(side="left", padx=(0, 8))

        error_label = ctk.CTkLabel(self.content_frame, text="", font=(FONT_FAMILY, 11), text_color=COLOUR_RED)

        def add_user():
            username = username_entry.get().strip()
            password = password_entry.get()
            role = role_combo.get()

            is_valid, message = validate_username(username)
            if not is_valid:
                error_label.configure(text=message)
                error_label.pack(anchor="w", pady=(0, 5))
                return

            is_valid, message = validate_password(password)
            if not is_valid:
                error_label.configure(text=message)
                error_label.pack(anchor="w", pady=(0, 5))
                return

            created = self.auth.create_user(username, password, role)
            if not created:
                error_label.configure(text="That username is already taken")
                error_label.pack(anchor="w", pady=(0, 5))
                return
            error_label.configure(text="")
            self._render_users_tab()

        add_btn = ctk.CTkButton(
            add_row, text="+ Add User", font=(FONT_FAMILY, 12, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, corner_radius=16,
            height=32, width=110, command=add_user
        )
        add_btn.pack(side="left")

        style = ttk.Style()
        style.configure("Users.Treeview", font=(FONT_FAMILY, 11), rowheight=28)
        style.configure("Users.Treeview.Heading", font=(FONT_FAMILY, 11, "bold"))

        columns = ("id", "username", "role", "status", "attempts")
        tree = ttk.Treeview(self.content_frame, columns=columns, show="headings", style="Users.Treeview", height=10)
        tree.heading("id", text="ID")
        tree.heading("username", text="Username")
        tree.heading("role", text="Role")
        tree.heading("status", text="Status")
        tree.heading("attempts", text="Failed Attempts")
        tree.column("id", width=50, anchor="center")
        tree.column("username", width=160)
        tree.column("role", width=90, anchor="center")
        tree.column("status", width=100, anchor="center")
        tree.column("attempts", width=110, anchor="center")
        tree.pack(fill="both", expand=True, pady=(0, 10))

        for user_id, username, role, is_active, attempts in self.auth.get_all_users():
            status = "Active" if is_active else "Deactivated"
            tree.insert("", "end", values=(user_id, username, role, status, attempts))

        def get_selected_user_id():
            sel = tree.selection()
            if not sel:
                return None
            return int(tree.item(sel[0], "values")[0])

        action_row = ctk.CTkFrame(self.content_frame, fg_color=COLOUR_BG)
        action_row.pack(fill="x")

        def toggle_active():
            user_id = get_selected_user_id()
            if user_id is None:
                return
            current_active = self.db.run_query(
                "SELECT is_active FROM Users WHERE user_id=?", (user_id,)
            )[0][0]
            self.auth.set_active(user_id, not current_active)
            self._render_users_tab()

        toggle_btn = ctk.CTkButton(
            action_row, text="Activate / Deactivate", font=(FONT_FAMILY, 12),
            fg_color="#e0e0e0", text_color=COLOUR_BLACK, hover_color="#cccccc",
            corner_radius=16, height=32, command=toggle_active
        )
        toggle_btn.pack(side="left", padx=(0, 8))

        def open_reset_dialog():
            user_id = get_selected_user_id()
            if user_id is None:
                return
            self._open_password_reset_dialog(user_id)

        reset_btn = ctk.CTkButton(
            action_row, text="Reset Password", font=(FONT_FAMILY, 12),
            fg_color="#d8ab81", text_color=COLOUR_BLACK, hover_color="#c99a70",
            corner_radius=16, height=32, command=open_reset_dialog
        )
        reset_btn.pack(side="left")

        def open_edit_dialog():
            user_id = get_selected_user_id()
            if user_id is None:
                return
            self._open_edit_account_dialog(user_id)

        edit_btn = ctk.CTkButton(
            action_row, text="Edit Account", font=(FONT_FAMILY, 12),
            fg_color="#e0e0e0", text_color=COLOUR_BLACK, hover_color="#cccccc",
            corner_radius=16, height=32, command=open_edit_dialog
        )
        edit_btn.pack(side="left", padx=(8, 0))

    def _open_edit_account_dialog(self, user_id):
        """Edit a user's username and role (FR13: edit account details)."""
        current = self.db.run_query(
            "SELECT username, role FROM Users WHERE user_id=?", (user_id,)
        )
        if not current:
            return
        current_username, current_role = current[0]

        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Account")
        dialog.geometry("320x260")
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="Username", font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK
        ).pack(anchor="w", padx=20, pady=(20, 0))
        username_entry = ctk.CTkEntry(dialog, font=(FONT_FAMILY, 12), width=260)
        username_entry.insert(0, current_username)
        username_entry.pack(padx=20, pady=(5, 15))

        ctk.CTkLabel(
            dialog, text="Role", font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK
        ).pack(anchor="w", padx=20)
        role_combo = ctk.CTkComboBox(dialog, values=["Staff", "Admin"], font=(FONT_FAMILY, 12), width=260)
        role_combo.set(current_role)
        role_combo.pack(padx=20, pady=(5, 15))

        error_label = ctk.CTkLabel(dialog, text="", font=(FONT_FAMILY, 10), text_color=COLOUR_RED)
        error_label.pack()

        def confirm_edit():
            new_username = username_entry.get().strip()
            new_role = role_combo.get()

            is_valid, message = validate_username(new_username)
            if not is_valid:
                error_label.configure(text=message)
                return

            success, message = self.auth.update_user(user_id, new_username, new_role)
            if not success:
                error_label.configure(text=message)
                return

            dialog.destroy()
            self._render_users_tab()

        confirm_btn = ctk.CTkButton(
            dialog, text="Save Changes", font=(FONT_FAMILY, 12, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, corner_radius=16,
            height=34, command=confirm_edit
        )
        confirm_btn.pack(pady=10)

    def _open_password_reset_dialog(self, user_id):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Reset Password")
        dialog.geometry("320x220")
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="New Password", font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK
        ).pack(anchor="w", padx=20, pady=(20, 0))

        new_pw_entry = ctk.CTkEntry(dialog, show="*", font=(FONT_FAMILY, 12), width=260)
        new_pw_entry.pack(padx=20, pady=(5, 15))

        error_label = ctk.CTkLabel(dialog, text="", font=(FONT_FAMILY, 10), text_color=COLOUR_RED)
        error_label.pack()

        def confirm_reset():
            new_password = new_pw_entry.get()
            is_valid, message = validate_password(new_password)
            if not is_valid:
                error_label.configure(text=message)
                return
            self.auth.reset_password(user_id, new_password)
            dialog.destroy()
            self._render_users_tab()

        confirm_btn = ctk.CTkButton(
            dialog, text="Reset Password", font=(FONT_FAMILY, 12, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, corner_radius=16,
            height=34, command=confirm_reset
        )
        confirm_btn.pack(pady=10)

    # ------------------------------------------------------------------
    # Backup & Export (Criterion 5, Possible Errors: DB corruption/loss
    # is high-impact with no recovery option in the original scope)
    # ------------------------------------------------------------------

    def _render_backup_tab(self):
        info_label = ctk.CTkLabel(
            self.content_frame,
            text="Back up the database file, or export the core records to CSV.",
            font=(FONT_FAMILY, 13),
            text_color=COLOUR_BLACK
        )
        info_label.pack(anchor="w", pady=(0, 5))

        note_label = ctk.CTkLabel(
            self.content_frame,
            text="A backup copies the entire quote_system.db file, which can be\n"
                 "restored by replacing the file the app reads from. CSV export\n"
                 "produces plain-text copies of Customers, Quotes, Quote Line\n"
                 "Items and Jobs for use in a spreadsheet.",
            font=(FONT_FAMILY, 11), text_color="#888888", justify="left"
        )
        note_label.pack(anchor="w", pady=(0, 20))

        status_label = ctk.CTkLabel(
            self.content_frame, text="", font=(FONT_FAMILY, 11), text_color=COLOUR_GREEN
        )

        def show_status(text, is_error=False):
            status_label.configure(text=text, text_color=COLOUR_RED if is_error else COLOUR_GREEN)
            status_label.pack(anchor="w", pady=(10, 0))

        def run_backup():
            default_name = f"orbost_backup_{datetime.today().strftime('%Y-%m-%d_%H%M')}.db"
            destination = filedialog.asksaveasfilename(
                title="Save Database Backup",
                defaultextension=".db",
                initialfile=default_name,
                filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
            )
            if not destination:
                return  # user cancelled
            try:
                self.db.backup_database(destination)
                show_status(f"Backup saved to {destination}")
            except Exception:
                show_status("Backup failed - check the destination is writable", is_error=True)

        def run_export():
            destination_folder = filedialog.askdirectory(title="Choose Export Folder")
            if not destination_folder:
                return  # user cancelled
            try:
                exported = self.db.export_all_to_csv(destination_folder)
                show_status(f"Exported {len(exported)} CSV file(s) to {destination_folder}")
            except Exception:
                show_status("Export failed - check the destination is writable", is_error=True)

        button_row = ctk.CTkFrame(self.content_frame, fg_color=COLOUR_BG)
        button_row.pack(fill="x")

        backup_btn = ctk.CTkButton(
            button_row, text="Backup Database", font=(FONT_FAMILY, 12, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, corner_radius=16,
            height=34, width=170, command=run_backup
        )
        backup_btn.pack(side="left", padx=(0, 8))

        export_btn = ctk.CTkButton(
            button_row, text="Export All Data to CSV", font=(FONT_FAMILY, 12, "bold"),
            fg_color="#d8ab81", text_color=COLOUR_BLACK, corner_radius=16,
            height=34, width=190, command=run_export
        )
        export_btn.pack(side="left")