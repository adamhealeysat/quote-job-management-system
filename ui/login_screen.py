"""
ui/login_screen.py

Login screen for the Orbost Auto Electrics Quote & Job Management System.
Built with CustomTkinter to match Mock-up 1 (Criterion 5): rounded fields
and button, green brand title, subtitle, red error message.
"""

import customtkinter as ctk

# Brand colours from Mood Board (Criterion 4)
COLOUR_GREEN = "#00bf63"
COLOUR_BLACK = "#000000"
COLOUR_RED = "#ff3131"
COLOUR_BG = "#f5f5f5"

# Font family used throughout the app (Mood Board, Criterion 4).
# Requires "Canva Sans" to be installed on the system as a TrueType font.
# If it isn't installed, Tkinter/CustomTkinter falls back to a default
# system font rather than raising an error.
FONT_FAMILY = "Canva Sans"

CORNER_RADIUS = 25


class LoginScreen(ctk.CTkFrame):
    """
    Login screen frame. Pass in an AuthManager instance and a callback
    function to run when login succeeds (on_login_success receives the
    username and role).
    """

    def __init__(self, parent, auth_manager, on_login_success):
        super().__init__(parent, fg_color=COLOUR_BG)
        self.auth_manager = auth_manager
        self.on_login_success = on_login_success

        self.pack(fill="both", expand=True)
        self._build_widgets()

    def _build_widgets(self):
        # Application title
        title_label = ctk.CTkLabel(
            self, text="Orbost Auto Electrics",
            font=(FONT_FAMILY, 20, "bold"), text_color=COLOUR_GREEN
        )
        title_label.pack(pady=(40, 0))

        # Subtitle
        subtitle_label = ctk.CTkLabel(
            self, text="Job Management System",
            font=(FONT_FAMILY, 16), text_color=COLOUR_BLACK
        )
        subtitle_label.pack(pady=(0, 30))

        # Username field
        username_label = ctk.CTkLabel(
            self, text="Username*", font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK, anchor="w"
        )
        username_label.pack(fill="x", padx=60)
        self.username_entry = ctk.CTkEntry(
            self, placeholder_text="Enter username",
            font=(FONT_FAMILY, 12), corner_radius=CORNER_RADIUS, height=36
        )
        self.username_entry.pack(fill="x", padx=60, pady=(0, 15))

        # Password field
        password_label = ctk.CTkLabel(
            self, text="Password*", font=(FONT_FAMILY, 12), text_color=COLOUR_BLACK, anchor="w"
        )
        password_label.pack(fill="x", padx=60)
        self.password_entry = ctk.CTkEntry(
            self, placeholder_text="Enter password", show="*",
            font=(FONT_FAMILY, 12), corner_radius=CORNER_RADIUS, height=36
        )
        self.password_entry.pack(fill="x", padx=60, pady=(0, 20))
        # Pressing Enter in the password field triggers login
        self.password_entry.bind("<Return>", lambda event: self._handle_login())

        # Login button
        login_button = ctk.CTkButton(
            self, text="Login", font=(FONT_FAMILY, 16, "bold"),
            fg_color=COLOUR_GREEN, text_color=COLOUR_BLACK, hover_color="#00a855",
            corner_radius=CORNER_RADIUS, height=44,
            command=self._handle_login
        )
        login_button.pack(padx=60, fill="x", pady=(0, 10))

        # Error message label (hidden until needed)
        self.error_label = ctk.CTkLabel(
            self, text="", font=(FONT_FAMILY, 10), text_color=COLOUR_RED
        )
        self.error_label.pack()

    def _handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.error_label.configure(text="Please enter both username and password")
            return

        result = self.auth_manager.login(username, password)

        if result["success"]:
            self.error_label.configure(text="")
            self.on_login_success(username, result["role"])
        else:
            self.error_label.configure(text=result["message"])
            self.password_entry.delete(0, "end")


def _center_window(window, width, height):
    """Centre a window on the screen."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


if __name__ == "__main__":
    # Standalone test of the login screen
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from database import DatabaseManager
    from auth import AuthManager

    db = DatabaseManager()
    db.connect()
    db.create_tables()
    auth = AuthManager(db)
    auth.create_user("todd", "changeme123", "Admin")  # no-op if already exists

    def on_success(username, role):
        print(f"Logged in as {username} ({role})")
        root.destroy()

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")

    root = ctk.CTk()
    root.title("Orbost Auto Electrics")
    root.configure(fg_color=COLOUR_BG)
    root.resizable(False, False)
    _center_window(root, 400, 400)

    LoginScreen(root, auth, on_success)

    root.mainloop()
    db.close()