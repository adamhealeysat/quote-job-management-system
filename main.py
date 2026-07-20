"""
main.py

Entry point for the Orbost Auto Electrics Quote & Job Management System.
Launches the login screen, then swaps to the dashboard on success.
"""

import customtkinter as ctk

from database import DatabaseManager
from auth import AuthManager
from ui.login_screen import LoginScreen, COLOUR_BG, COLOUR_GREEN, FONT_FAMILY, _center_window
from ui.dashboard import Dashboard


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Orbost Auto Electrics - Job Manager")
        self.configure(fg_color=COLOUR_BG)
        self.resizable(False, False)
        _center_window(self, 400, 400)

        # Set up database + auth
        self.db = DatabaseManager()
        self.db.connect()
        self.db.create_tables()
        self.auth = AuthManager(self.db)

        # One-time seed admin account (safe to leave in — create_user
        # returns False and does nothing if 'todd' already exists)
        self.auth.create_user("todd", "changeme123", "Admin")

        self.current_frame = None
        self.show_login()

    def show_login(self):
        self._clear_frame()
        self.geometry("400x400")
        _center_window(self, 400, 400)
        self.current_frame = LoginScreen(self, self.auth, self.show_dashboard)

    def show_dashboard(self, username, role):
        self._clear_frame()
        # Dashboard needs more room than the login window
        self.geometry("900x600")
        _center_window(self, 900, 600)

        self.current_frame = Dashboard(self, self.db, self.auth, username, role, self.show_login)

    def _clear_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()
            self.current_frame = None

    def on_close(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")

    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()