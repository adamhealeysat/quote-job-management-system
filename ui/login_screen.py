"""
ui/login_screen.py

Login screen for the Orbost Auto Electrics Quote & Job Management System.
Built to match Mock-up 1 (Criterion 5): 400x400 centred window,
green brand title, subtitle, username/password fields, login button,
red error message.
"""

import tkinter as tk
from tkinter import font as tkfont

# Brand colours from Mood Board (Criterion 4)
COLOUR_GREEN = "#00bf63"
COLOUR_BLACK = "#000000"
COLOUR_RED = "#ff3131"
COLOUR_BG = "#f5f5f5"

# Font family used throughout the app (Mood Board, Criterion 4).
# Requires "Canva Sans" to be installed on the system as a TrueType font.
# If it isn't installed, Tkinter silently falls back to a default system font
# rather than raising an error.
FONT_FAMILY = "Canva Sans"


class LoginScreen(tk.Frame):
    """
    Login screen frame. Pass in an AuthManager instance and a callback
    function to run when login succeeds (on_login_success receives the
    username and role).
    """

    def __init__(self, parent, auth_manager, on_login_success):
        super().__init__(parent, bg=COLOUR_BG)
        self.auth_manager = auth_manager
        self.on_login_success = on_login_success

        self.pack(fill="both", expand=True)
        self._build_widgets()

    def _build_widgets(self):
        title_font = tkfont.Font(family=FONT_FAMILY, size=20, weight="bold")
        subtitle_font = tkfont.Font(family=FONT_FAMILY, size=16)
        label_font = tkfont.Font(family=FONT_FAMILY, size=12)
        button_font = tkfont.Font(family=FONT_FAMILY, size=16, weight="bold")
        error_font = tkfont.Font(family=FONT_FAMILY, size=10)

        # Application title
        title_label = tk.Label(
            self, text="Orbost Auto Electrics",
            font=title_font, fg=COLOUR_GREEN, bg=COLOUR_BG
        )
        title_label.pack(pady=(40, 0))

        # Subtitle
        subtitle_label = tk.Label(
            self, text="Job Management System",
            font=subtitle_font, fg=COLOUR_BLACK, bg=COLOUR_BG
        )
        subtitle_label.pack(pady=(0, 30))

        # Username field
        username_label = tk.Label(
            self, text="Username*", font=label_font, fg=COLOUR_BLACK, bg=COLOUR_BG, anchor="w"
        )
        username_label.pack(fill="x", padx=60)
        self.username_entry = tk.Entry(self, font=label_font)
        self.username_entry.pack(fill="x", padx=60, pady=(0, 15))

        # Password field
        password_label = tk.Label(
            self, text="Password*", font=label_font, fg=COLOUR_BLACK, bg=COLOUR_BG, anchor="w"
        )
        password_label.pack(fill="x", padx=60)
        self.password_entry = tk.Entry(self, font=label_font, show="*")
        self.password_entry.pack(fill="x", padx=60, pady=(0, 20))
        # Pressing Enter in the password field triggers login
        self.password_entry.bind("<Return>", lambda event: self._handle_login())

        # Login button
        login_button = tk.Button(
            self, text="Login", font=button_font, fg=COLOUR_BLACK,
            command=self._handle_login, cursor="hand2"
        )
        login_button.pack(pady=(0, 10))

        # Error message label (hidden until needed)
        self.error_label = tk.Label(
            self, text="", font=error_font, fg=COLOUR_RED, bg=COLOUR_BG
        )
        self.error_label.pack()

    def _handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.error_label.config(text="Please enter both username and password")
            return

        result = self.auth_manager.login(username, password)

        if result["success"]:
            self.error_label.config(text="")
            self.on_login_success(username, result["role"])
        else:
            self.error_label.config(text=result["message"])
            self.password_entry.delete(0, tk.END)


def _center_window(window, width, height):
    """Centre a Tkinter window on the screen."""
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

    root = tk.Tk()
    root.title("Orbost Auto Electrics")
    root.configure(bg=COLOUR_BG)
    root.resizable(False, False)
    _center_window(root, 400, 400)

    # Warn (in the terminal, not the UI) if Canva Sans isn't actually installed
    if FONT_FAMILY not in tkfont.families():
        print(f"Note: '{FONT_FAMILY}' is not installed on this system. "
              f"Tkinter will fall back to a default font instead.")

    LoginScreen(root, auth, on_success)

    root.mainloop()
    db.close()