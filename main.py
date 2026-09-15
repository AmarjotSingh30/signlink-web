import tkinter as tk
from tkinter import font, ttk, messagebox, simpledialog
import subprocess
import sys
import threading
import sqlite3
import bcrypt
import secrets
import json
import os
import re

class SignLinkApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SignLink - Secure Access")
        
        self.window_width = 850
        self.window_height = 550
        self.root.geometry(f"{self.window_width}x{self.window_height}")

        self.sidebar_bg = "#020617"        
        self.main_bg = "#0f172a"           
        self.card_bg = "#1e293b"           
        self.card_hover = "#334155"        
        self.text_primary = "#f8fafc"      
        self.text_secondary = "#94a3b8"    
        self.accent_green = "#10b981"      
        self.accent_blue = "#3b82f6"       
        self.accent_blue_hover = "#2563eb" 
        self.accent_red = "#ef4444"        
        self.accent_red_hover = "#dc2626"  
        self.accent_warn = "#d97706"       

        self.root.configure(bg=self.main_bg)

        self.logo_font = font.Font(family="Segoe UI", size=26, weight="bold")
        self.header_font = font.Font(family="Segoe UI", size=22, weight="bold")
        self.normal_font = font.Font(family="Segoe UI", size=11)
        self.small_font = ("Segoe UI", 10, "italic")
        self.btn_font = font.Font(family="Segoe UI", size=12, weight="bold")

        self.current_user_id = None
        self.current_email = None
        self.current_role = None
        self.current_view = None 
        self.nav_labels = {}     

        self.init_database()
        self.center_window()
        
        if self.validate_existing_session():
            self.build_app_shell()
        else:
            self.build_auth_ui()

    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.window_width // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.window_height // 2)
        self.root.geometry(f'{self.window_width}x{self.window_height}+{x}+{y}')

    def init_database(self):
        conn = sqlite3.connect('signlink.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT, role TEXT, session_token TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS progress 
                     (user_id INTEGER PRIMARY KEY, current_index INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS translations 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, text TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS password_resets 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

    def validate_email(self, email):
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email):
            return False, "Please enter a valid email address (e.g., user@domain.com)."
        return True, ""

    def validate_password_strength(self, password):
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter."
        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one number."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character (!@#$%)."
        return True, ""

    def hash_password(self, plain_text_password):
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(plain_text_password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, plain_text_password, hashed_password):
        return bcrypt.checkpw(plain_text_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def generate_session_token(self):
        return secrets.token_hex(32)

    def validate_existing_session(self):
        if not os.path.exists("session.json"): return False
        try:
            with open("session.json", "r") as f:
                data = json.load(f)
                stored_id, stored_token = data.get("user_id"), data.get("session_token")
            if not stored_id or not stored_token: return False
                
            conn = sqlite3.connect('signlink.db')
            c = conn.cursor()
            c.execute("SELECT email, role FROM users WHERE id=? AND session_token=?", (stored_id, stored_token))
            user = c.fetchone()
            conn.close()
            
            if user:
                self.current_user_id = stored_id
                self.current_email = user[0]
                self.current_role = user[1]
                return True
            return False
        except: return False

    # ==========================================
    # AUTHENTICATION UI
    # ==========================================
    def build_auth_ui(self):
        for widget in self.root.winfo_children(): widget.destroy()
        self.root.title("SignLink - Secure Access")
        
        sidebar = tk.Frame(self.root, bg=self.sidebar_bg, width=350)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Welcome to", font=self.normal_font, bg=self.sidebar_bg, fg=self.text_primary).pack(pady=(180, 0))
        tk.Label(sidebar, text="SignLink", font=self.logo_font, bg=self.sidebar_bg, fg=self.accent_blue).pack(pady=(0, 10))

        mission_text = "Bridging the communication\nConnecting signs to words\nand people to people."
        tk.Label(sidebar, text=mission_text, font=self.small_font, bg=self.sidebar_bg, fg=self.text_secondary, justify="center").pack(side="bottom", pady=40)

        self.auth_frame = tk.Frame(self.root, bg=self.main_bg)
        self.auth_frame.pack(side="left", fill="both", expand=True) 
        self.show_login_frame()

    def create_modern_entry(self, parent, is_password=False):
        frame = tk.Frame(parent, bg=self.main_bg)
        frame.pack(fill="x", pady=(5, 15))
        
        entry = tk.Entry(
            frame, font=("Segoe UI", 12), bg=self.card_bg, fg=self.text_primary, 
            insertbackground="white", relief="flat", highlightthickness=2,
            highlightbackground=self.card_hover, highlightcolor=self.accent_blue,
            show="●" if is_password else ""
        )
        entry.pack(fill="x", ipady=8)
        return entry, frame

    def show_login_frame(self):
        for widget in self.auth_frame.winfo_children(): widget.destroy()
        form_bg = "#0f172a" 
        container = tk.Frame(self.auth_frame, bg=form_bg, padx=50, pady=40)
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(container, text="Welcome Back", font=("Segoe UI", 28, "bold"), bg=form_bg, fg=self.text_primary).pack(pady=(0, 5))
        tk.Label(container, text="Please enter your details to sign in.", font=("Segoe UI", 11), bg=form_bg, fg=self.text_secondary).pack(pady=(0, 30))

        tk.Label(container, text="Email Address", font=("Segoe UI", 10, "bold"), bg=form_bg, fg=self.text_secondary).pack(anchor="w")
        self.entry_login_email, _ = self.create_modern_entry(container)

        tk.Label(container, text="Password", font=("Segoe UI", 10, "bold"), bg=form_bg, fg=self.text_secondary).pack(anchor="w")
        self.entry_login_pass, pw_frame = self.create_modern_entry(container, is_password=True)
        
        forgot_pw = tk.Label(container, text="Forgot password?", font=("Segoe UI", 9, "underline"), bg=form_bg, fg=self.accent_blue, cursor="hand2")
        forgot_pw.pack(anchor="e", pady=(0, 20))
        forgot_pw.bind("<Enter>", lambda e: forgot_pw.config(fg="#60a5fa"))
        forgot_pw.bind("<Leave>", lambda e: forgot_pw.config(fg=self.accent_blue))
        forgot_pw.bind("<Button-1>", lambda e: self.trigger_forgot_password())

        tk.Button(container, text="Sign In", font=("Segoe UI", 12, "bold"), bg=self.accent_blue, fg="white", activebackground=self.accent_blue_hover, relief="flat", cursor="hand2", command=self.process_login).pack(fill="x", ipady=10, pady=(0, 20))

        divider_frame = tk.Frame(container, bg=form_bg)
        divider_frame.pack(fill="x", pady=10)
        tk.Frame(divider_frame, bg=self.card_hover, height=1).pack(side="left", fill="x", expand=True)
        tk.Label(divider_frame, text=" OR ", font=("Segoe UI", 9), bg=form_bg, fg=self.text_secondary).pack(side="left", padx=10)
        tk.Frame(divider_frame, bg=self.card_hover, height=1).pack(side="right", fill="x", expand=True)

        switch_frame = tk.Frame(container, bg=form_bg)
        switch_frame.pack(pady=(20, 0))
        tk.Label(switch_frame, text="Don't have an account?", font=("Segoe UI", 10), bg=form_bg, fg=self.text_secondary).pack(side="left")
        
        reg_btn = tk.Label(switch_frame, text="Sign up", font=("Segoe UI", 10, "bold"), bg=form_bg, fg=self.text_primary, cursor="hand2")
        reg_btn.pack(side="left", padx=(5, 0))
        reg_btn.bind("<Button-1>", lambda e: self.show_register_frame())
        reg_btn.bind("<Enter>", lambda e: reg_btn.config(fg=self.accent_blue))
        reg_btn.bind("<Leave>", lambda e: reg_btn.config(fg=self.text_primary))

    def show_register_frame(self):
        for widget in self.auth_frame.winfo_children(): widget.destroy()
        form_bg = "#0f172a"
        container = tk.Frame(self.auth_frame, bg=form_bg, padx=50, pady=40)
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(container, text="Create an Account", font=("Segoe UI", 28, "bold"), bg=form_bg, fg=self.text_primary).pack(pady=(0, 5))
        tk.Label(container, text="Join the SignLink platform today.", font=("Segoe UI", 11), bg=form_bg, fg=self.text_secondary).pack(pady=(0, 20))

        tk.Label(container, text="Email Address", font=("Segoe UI", 10, "bold"), bg=form_bg, fg=self.text_secondary).pack(anchor="w")
        self.entry_reg_email, _ = self.create_modern_entry(container)

        tk.Label(container, text="Create Password", font=("Segoe UI", 10, "bold"), bg=form_bg, fg=self.text_secondary).pack(anchor="w")
        self.entry_reg_pass, pw_frame = self.create_modern_entry(container, is_password=True)
        
        tk.Label(container, text="Requires: 8+ chars, 1 uppercase, 1 number, 1 symbol.", font=("Segoe UI", 8), bg=form_bg, fg=self.text_secondary).pack(anchor="w", pady=(0, 20))

        tk.Button(container, text="Create Account", font=("Segoe UI", 12, "bold"), bg=self.accent_green, fg="white", activebackground="#059669", relief="flat", cursor="hand2", command=self.process_register).pack(fill="x", ipady=10, pady=(10, 20))

        divider_frame = tk.Frame(container, bg=form_bg)
        divider_frame.pack(fill="x", pady=10)
        tk.Frame(divider_frame, bg=self.card_hover, height=1).pack(side="left", fill="x", expand=True)
        tk.Label(divider_frame, text=" OR ", font=("Segoe UI", 9), bg=form_bg, fg=self.text_secondary).pack(side="left", padx=10)
        tk.Frame(divider_frame, bg=self.card_hover, height=1).pack(side="right", fill="x", expand=True)

        switch_frame = tk.Frame(container, bg=form_bg)
        switch_frame.pack(pady=(20, 0))
        tk.Label(switch_frame, text="Already have an account?", font=("Segoe UI", 10), bg=form_bg, fg=self.text_secondary).pack(side="left")
        
        log_btn = tk.Label(switch_frame, text="Sign in", font=("Segoe UI", 10, "bold"), bg=form_bg, fg=self.text_primary, cursor="hand2")
        log_btn.pack(side="left", padx=(5, 0))
        log_btn.bind("<Button-1>", lambda e: self.show_login_frame())
        log_btn.bind("<Enter>", lambda e: log_btn.config(fg=self.accent_blue))
        log_btn.bind("<Leave>", lambda e: log_btn.config(fg=self.text_primary))

    def trigger_forgot_password(self):
        email = simpledialog.askstring("Account Recovery", "Enter your registered Email Address:")
        if email:
            email = email.strip()
            conn = sqlite3.connect('signlink.db')
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE email=?", (email,))
            user = c.fetchone()
            if user:
                try:
                    c.execute("INSERT INTO password_resets (email, status) VALUES (?, 'Pending')", (email,))
                    conn.commit()
                    messagebox.showinfo("Ticket Submitted", f"A reset ticket for {email} has been sent to the Admin Dashboard.\n\nPlease contact your instructor/admin to retrieve your temporary password.")
                except sqlite3.IntegrityError:
                    messagebox.showinfo("Ticket Pending", "You already have a pending password reset request. Please wait for the Admin to process it.")
            else:
                messagebox.showwarning("System Error", "That email address is not registered in the system.")
            conn.close()

    def process_login(self):
        email = self.entry_login_email.get().strip()
        password = self.entry_login_pass.get().strip()
        if not email or not password:
            messagebox.showwarning("Validation Error", "All fields are required.")
            return

        conn = sqlite3.connect('signlink.db')
        c = conn.cursor()
        c.execute("SELECT id, email, password, role FROM users WHERE email=?", (email,))
        user = c.fetchone()
        
        if user and self.check_password(password, user[2]):
            self.current_user_id = user[0]
            self.current_email = user[1]
            self.current_role = user[3]
            new_token = self.generate_session_token()
            c.execute("UPDATE users SET session_token=? WHERE id=?", (new_token, self.current_user_id))
            conn.commit()
            self.create_session_file(new_token)
            self.build_app_shell()
        else:
            messagebox.showerror("Access Denied", "Invalid email address or password.")
        conn.close()

    def process_register(self):
        email = self.entry_reg_email.get().strip()
        password = self.entry_reg_pass.get().strip()

        is_valid_email, email_msg = self.validate_email(email)
        if not is_valid_email:
            messagebox.showwarning("Invalid Email", email_msg)
            return

        is_valid_pass, pass_msg = self.validate_password_strength(password)
        if not is_valid_pass:
            messagebox.showwarning("Weak Password", pass_msg)
            return

        hashed_pw = self.hash_password(password)
        new_token = self.generate_session_token()

        conn = sqlite3.connect('signlink.db')
        c = conn.cursor()
        try:
            c.execute("SELECT COUNT(*) FROM users")
            user_count = c.fetchone()[0]
            assigned_role = "Admin" if user_count == 0 else "User"

            c.execute("INSERT INTO users (email, password, role, session_token) VALUES (?, ?, ?, ?)", (email, hashed_pw, assigned_role, new_token))
            user_id = c.lastrowid
            c.execute("INSERT INTO progress (user_id, current_index) VALUES (?, ?)", (user_id, 0))
            conn.commit()
            
            self.current_user_id = user_id
            self.current_email = email
            self.current_role = assigned_role
            self.create_session_file(new_token)
            self.build_app_shell()
        except sqlite3.IntegrityError:
            messagebox.showerror("Registration Error", "An account with this email already exists.")
        finally:
            conn.close()

    def create_session_file(self, token):
        session_data = {"user_id": self.current_user_id, "email": self.current_email, "session_token": token}
        with open("session.json", "w") as f:
            json.dump(session_data, f)

    def logout(self):
        if self.current_user_id:
            conn = sqlite3.connect('signlink.db')
            c = conn.cursor()
            c.execute("UPDATE users SET session_token=NULL WHERE id=?", (self.current_user_id,))
            conn.commit()
            conn.close()
        if os.path.exists("session.json"): os.remove("session.json")
        self.current_user_id = None
        self.current_email = None
        self.current_role = None
        self.current_view = None
        self.nav_labels.clear()
        self.build_auth_ui()

    def get_user_stats(self):
        try:
            conn = sqlite3.connect('signlink.db')
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM translations WHERE user_id=?", (self.current_user_id,))
            trans_count = c.fetchone()[0]
            c.execute("SELECT current_index FROM progress WHERE user_id=?", (self.current_user_id,))
            prog_row = c.fetchone()
            prog_index = prog_row[0] if prog_row else 0
            conn.close()
            return trans_count, prog_index
        except:
            return 0, 0
            
    def get_admin_stats(self):
        try:
            conn = sqlite3.connect('signlink.db')
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            user_count = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM translations")
            global_trans = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM password_resets WHERE status='Pending'")
            pending_resets = c.fetchone()[0]
            conn.close()
            return user_count, global_trans, pending_resets
        except:
            return 0, 0, 0

    # ==========================================
    # CORE APP SHELL & SIDEBAR ROUTING
    # ==========================================
    def build_app_shell(self):
        for widget in self.root.winfo_children(): widget.destroy()
        
        display_name = self.current_email.split('@')[0].capitalize()
        self.root.title(f"SignLink - Session Active")

        sidebar = tk.Frame(self.root, bg=self.sidebar_bg, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False) 

        tk.Label(sidebar, text="SignLink", font=self.logo_font, bg=self.sidebar_bg, fg=self.text_primary).pack(pady=(40, 5), anchor="center")
        tk.Label(sidebar, text="Connecting signs with words", font=self.normal_font, bg=self.sidebar_bg, fg=self.accent_blue).pack(anchor="center")
        tk.Frame(sidebar, bg=self.card_bg, height=1).pack(fill="x", padx=20, pady=25)

        tk.Label(sidebar, text=f"Active Profile:", font=("Segoe UI", 9), bg=self.sidebar_bg, fg=self.text_secondary).pack(anchor="w", padx=25)
        role_color = self.accent_red if self.current_role == "Admin" else self.accent_green
        tk.Label(sidebar, text=f"{display_name} [{self.current_role}]", font=font.Font(family="Segoe UI", size=14, weight="bold"), bg=self.sidebar_bg, fg=role_color).pack(anchor="w", padx=25, pady=(0, 15))

        tk.Label(sidebar, text="MAIN MENU", font=("Segoe UI", 8, "bold"), bg=self.sidebar_bg, fg=self.text_secondary).pack(anchor="w", padx=25, pady=(10, 5))
        
        self.create_nav_item(sidebar, "Dashboard", "🏠  Dashboard", self.render_dashboard)
        self.create_nav_item(sidebar, "Profile", "👤  Profile Settings", self.render_profile)
        self.create_nav_item(sidebar, "Preferences", "⚙️  Preferences", self.render_preferences)
        self.create_nav_item(sidebar, "Help", "❓  Help & Support", self.render_help)

        self.btn_quit = tk.Button(sidebar, text="⏻ SECURE LOGOUT", font=("Segoe UI", 10, "bold"), bg=self.sidebar_bg, fg=self.accent_red, activebackground=self.accent_red_hover, activeforeground="white", relief="flat", cursor="hand2", command=self.logout, pady=10)
        self.btn_quit.pack(side="bottom", fill="x", pady=20, padx=20)
        self.btn_quit.bind("<Enter>", lambda e: self.btn_quit.config(bg=self.accent_red, fg="white") if self.btn_quit['state'] == 'normal' else None)
        self.btn_quit.bind("<Leave>", lambda e: self.btn_quit.config(bg=self.sidebar_bg, fg=self.accent_red) if self.btn_quit['state'] == 'normal' else None)

        self.main_content = tk.Frame(self.root, bg=self.main_bg)
        self.main_content.pack(side="left", fill="both", expand=True)

        self.switch_view("Dashboard", self.render_dashboard)

    def create_nav_item(self, parent, view_name, label_text, command):
        lbl = tk.Label(parent, text=label_text, font=("Segoe UI", 11), bg=self.sidebar_bg, fg=self.text_secondary, anchor="w", padx=20, pady=8, cursor="hand2")
        lbl.pack(fill="x", padx=15, pady=2)
        
        self.nav_labels[view_name] = lbl
        
        lbl.bind("<Button-1>", lambda e, v=view_name, c=command: self.switch_view(v, c))
        lbl.bind("<Enter>", lambda e, v=view_name, l=lbl: self.on_nav_enter(v, l))
        lbl.bind("<Leave>", lambda e, v=view_name, l=lbl: self.on_nav_leave(v, l))

    def on_nav_enter(self, view_name, lbl):
        if self.current_view != view_name:
            lbl.config(bg=self.card_bg, fg=self.text_primary)

    def on_nav_leave(self, view_name, lbl):
        if self.current_view != view_name:
            lbl.config(bg=self.sidebar_bg, fg=self.text_secondary)

    def switch_view(self, view_name, command_func):
        self.current_view = view_name
        
        for name, lbl in self.nav_labels.items():
            if name == view_name:
                lbl.config(bg=self.card_bg, fg=self.text_primary)
            else:
                lbl.config(bg=self.sidebar_bg, fg=self.text_secondary)
                
        for widget in self.main_content.winfo_children():
            widget.destroy()
            
        command_func()

    # ==========================================
    # VIEW 1: DASHBOARD
    # ==========================================
    def render_dashboard(self):
        display_name = self.current_email.split('@')[0].capitalize()
        role_color = self.accent_red if self.current_role == "Admin" else self.accent_green

        banner = tk.Frame(self.main_content, bg=self.card_bg)
        banner.pack(fill="x", padx=40, pady=(40, 20))
        tk.Label(banner, text=f"Welcome back, {display_name}.", font=("Segoe UI", 22, "bold"), bg=self.card_bg, fg=self.text_primary).pack(anchor="w", padx=30, pady=(20, 0))
        tk.Label(banner, text="", font=("Segoe UI", 11), bg=self.card_bg, fg=self.text_secondary).pack(anchor="w", padx=30, pady=(5, 20))

        grid_frame = tk.Frame(self.main_content, bg=self.main_bg)
        grid_frame.pack(fill="x", padx=35)

        if self.current_role == "Admin":
            self.admin_ui = self.create_grid_card(grid_frame, "🛡️", "Admin Control Center", "Manage platform users, roles, and global translation logs.", self.accent_red, self.launch_admin)
            self.admin_ui[0].pack(side="left", fill="both", expand=True, padx=5)
        else:
            self.interp_ui = self.create_grid_card(grid_frame, "🌐", "Sign Language Interpreter", "Intrepret signs into words", self.accent_green, self.launch_translator)
            self.interp_ui[0].pack(side="left", fill="both", expand=True, padx=5)

            self.tutor_ui = self.create_grid_card(grid_frame, "🧠", "Learn Sign Language", "Learn signs for communications", self.accent_blue, self.launch_tutor)
            self.tutor_ui[0].pack(side="left", fill="both", expand=True, padx=5)

        stats_frame = tk.Frame(self.main_content, bg=self.main_bg)
        stats_frame.pack(fill="both", expand=True, padx=40, pady=(30, 40))

        if self.current_role == "Admin":
            tk.Label(stats_frame, text="GLOBAL SYSTEM OVERVIEW", font=("Segoe UI", 10, "bold"), bg=self.main_bg, fg=self.text_secondary).pack(anchor="w", pady=(0, 10))
            stat_content = tk.Frame(stats_frame, bg=self.card_bg, padx=20, pady=20)
            stat_content.pack(fill="both", expand=True)
            
            user_count, global_trans, pending_resets = self.get_admin_stats()
            
            self.create_stat_column(stat_content, "Total Registered Users", f"{user_count} Users", self.accent_blue)
            self.create_stat_column(stat_content, "Global Translations", f"{global_trans} Logs", self.accent_green)
            
            reset_color = self.accent_red if pending_resets > 0 else self.text_secondary
            self.create_stat_column(stat_content, "Pending Reset Tickets", f"{pending_resets} Tickets", reset_color)

        else:
            tk.Label(stats_frame, text="YOUR ACTIVITY SUMMARY", font=("Segoe UI", 10, "bold"), bg=self.main_bg, fg=self.text_secondary).pack(anchor="w", pady=(0, 10))
            stat_content = tk.Frame(stats_frame, bg=self.card_bg, padx=20, pady=20)
            stat_content.pack(fill="both", expand=True)
            
            trans_count, prog_index = self.get_user_stats()
            self.create_stat_column(stat_content, "Total Translations", f"{trans_count} Logs", self.accent_blue)
            self.create_stat_column(stat_content, "Learning Progress", f"Level {prog_index}", self.accent_green)
            self.create_stat_column(stat_content, "Role", "USER", self.accent_green)

    # ==========================================
    # VIEW 2: PROFILE SETTINGS
    # ==========================================
    def render_profile(self):
        tk.Label(self.main_content, text="Profile Settings", font=("Segoe UI", 24, "bold"), bg=self.main_bg, fg=self.text_primary).pack(anchor="w", padx=40, pady=(40, 5))
        tk.Label(self.main_content, text="Manage your secure SignLink identity.", font=("Segoe UI", 11), bg=self.main_bg, fg=self.text_secondary).pack(anchor="w", padx=40, pady=(0, 30))

        card = tk.Frame(self.main_content, bg=self.card_bg, padx=40, pady=40)
        card.pack(fill="x", padx=40)

        tk.Label(card, text="ACCOUNT EMAIL", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.text_secondary).pack(anchor="w")
        tk.Label(card, text=self.current_email, font=("Segoe UI", 14), bg=self.card_bg, fg=self.text_primary).pack(anchor="w", pady=(0, 20))

        tk.Label(card, text="UNIQUE SYSTEM ID", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.text_secondary).pack(anchor="w")
        tk.Label(card, text=f"USR-000{self.current_user_id}-SLK", font=("Consolas", 14), bg=self.card_bg, fg=self.accent_blue).pack(anchor="w", pady=(0, 20))

        tk.Label(card, text="ASSIGNED ROLE", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.text_secondary).pack(anchor="w")
        tk.Label(card, text=self.current_role, font=("Segoe UI", 14), bg=self.card_bg, fg=self.accent_green if self.current_role != "Admin" else self.accent_red).pack(anchor="w", pady=(0, 30))

        tk.Button(card, text="Submit Password Reset Request", font=("Segoe UI", 10, "bold"), bg=self.card_hover, fg=self.text_primary, activebackground=self.sidebar_bg, activeforeground="white", relief="flat", cursor="hand2", command=self.submit_logged_in_reset).pack(anchor="w", ipady=5, ipadx=10)

    def submit_logged_in_reset(self):
        conn = sqlite3.connect('signlink.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO password_resets (email, status) VALUES (?, 'Pending')", (self.current_email,))
            conn.commit()
            messagebox.showinfo("Ticket Submitted", "A reset ticket has been sent to the Admin.\n\nYou will be securely logged out now. Please contact the Admin for your new password.")
            self.logout()
        except sqlite3.IntegrityError:
            messagebox.showinfo("Ticket Pending", "You already have a pending password reset request. Please wait for the Admin to process it.")
        finally:
            conn.close()

    # ==========================================
    # VIEW 3: PREFERENCES
    # ==========================================
    def render_preferences(self):
        tk.Label(self.main_content, text="System Preferences", font=("Segoe UI", 24, "bold"), bg=self.main_bg, fg=self.text_primary).pack(anchor="w", padx=40, pady=(40, 5))
        tk.Label(self.main_content, text="Customize your local application hardware and telemetry settings.", font=("Segoe UI", 11), bg=self.main_bg, fg=self.text_secondary).pack(anchor="w", padx=40, pady=(0, 30))

        card = tk.Frame(self.main_content, bg=self.card_bg, padx=40, pady=30)
        card.pack(fill="x", padx=40)

        self.create_pref_toggle(card, "Hardware Acceleration (GPU)", "Utilize local GPU resources for faster CNN gesture recognition.", checked=True)
        self.create_pref_toggle(card, "Telemetry Sync", "Automatically sync your translation logs to the local database.", checked=True)
        self.create_pref_toggle(card, "High Contrast Mode", "Increase UI visibility for accessibility purposes.", checked=False)
        self.create_pref_toggle(card, "Verbose Logging", "Enable deep system logs for developer debugging.", checked=False, is_last=True)

    def create_pref_toggle(self, parent, title, desc, checked=False, is_last=False):
        frame = tk.Frame(parent, bg=self.card_bg)
        frame.pack(fill="x", pady=(0, 15 if not is_last else 0))
        
        text_frame = tk.Frame(frame, bg=self.card_bg)
        text_frame.pack(side="left", fill="x", expand=True)
        tk.Label(text_frame, text=title, font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=self.text_primary).pack(anchor="w")
        tk.Label(text_frame, text=desc, font=("Segoe UI", 10), bg=self.card_bg, fg=self.text_secondary).pack(anchor="w")

        status = "ON" if checked else "OFF"
        color = self.accent_green if checked else self.text_secondary
        tk.Label(frame, text=status, font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=color).pack(side="right", padx=10)

    # ==========================================
    # VIEW 4: HELP & SUPPORT
    # ==========================================
    def render_help(self):
        tk.Label(self.main_content, text="Help & Support", font=("Segoe UI", 24, "bold"), bg=self.main_bg, fg=self.text_primary).pack(anchor="w", padx=40, pady=(40, 5))
        tk.Label(self.main_content, text="Need assistance with the SignLink Core Engine?", font=("Segoe UI", 11), bg=self.main_bg, fg=self.text_secondary).pack(anchor="w", padx=40, pady=(0, 30))

        card = tk.Frame(self.main_content, bg=self.card_bg, padx=40, pady=40)
        card.pack(fill="x", padx=40)

        tk.Label(card, text="For technical issues, database errors, or camera hardware failures, please contact the B.Tech Major Project engineering team.", font=("Segoe UI", 11), bg=self.card_bg, fg=self.text_secondary, wraplength=500, justify="left").pack(anchor="w", pady=(0, 30))

        tk.Label(card, text="Primary Administrator Email:", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_secondary).pack(anchor="w")
        tk.Label(card, text="admin@signlink.local", font=("Consolas", 14), bg=self.card_bg, fg=self.accent_blue).pack(anchor="w", pady=(0, 20))

        tk.Label(card, text="Current System Version:", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.text_secondary).pack(anchor="w")
        tk.Label(card, text="newly", font=("Segoe UI", 12), bg=self.card_bg, fg=self.text_primary).pack(anchor="w")

    # ==========================================
    # DASHBOARD HELPER FUNCTIONS (Emoji Alignment Fixed)
    # ==========================================
    def create_stat_column(self, parent, label, value, color):
        frame = tk.Frame(parent, bg=self.card_bg)
        frame.pack(side="left", expand=True, fill="both")
        tk.Label(frame, text=label, font=("Segoe UI", 10), bg=self.card_bg, fg=self.text_secondary).pack(anchor="center")
        tk.Label(frame, text=value, font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=color).pack(anchor="center", pady=(2,0))

    def create_grid_card(self, parent, icon_text, title, description, accent_color, command):
        card = tk.Frame(parent, bg=self.card_bg, cursor="hand2")
        tk.Frame(card, bg=accent_color, height=4).pack(fill="x")

        content = tk.Frame(card, bg=self.card_bg, padx=20, pady=30, cursor="hand2")
        content.pack(fill="both", expand=True)

        # Added leading space and explicit center anchor to fix Tkinter Emoji shift bug
        lbl_icon = tk.Label(content, text=f" {icon_text}", font=("Segoe UI", 36), bg=self.card_bg, fg=self.text_primary, cursor="hand2", justify="center")
        lbl_icon.pack(pady=(0, 10), anchor="center")
        
        lbl_title = tk.Label(content, text=title, font=("Segoe UI", 14, "bold"), bg=self.card_bg, fg=self.text_primary, cursor="hand2", justify="center")
        lbl_title.pack(anchor="center")
        
        lbl_desc = tk.Label(content, text=description, font=("Segoe UI", 10), bg=self.card_bg, fg=self.text_secondary, wraplength=200, justify="center", cursor="hand2")
        lbl_desc.pack(pady=(10, 0), anchor="center")

        ui_elements = (card, content, [lbl_icon, lbl_title, lbl_desc], icon_text)

        for el in [card, content, lbl_icon, lbl_title, lbl_desc]:
            el.bind("<Button-1>", lambda e: command() if card.winfo_name() not in ["disabled_interp", "disabled_tutor", "disabled_admin"] else None)
            el.bind("<Enter>", lambda e, elems=ui_elements: self.on_card_hover(elems, True))
            el.bind("<Leave>", lambda e, elems=ui_elements: self.on_card_hover(elems, False))
            
        return ui_elements

    def on_card_hover(self, ui_elements, is_hovering):
        card, content, labels, _ = ui_elements
        if card.winfo_name() in ["disabled_interp", "disabled_tutor", "disabled_admin"]: return 
        color = self.card_hover if is_hovering else self.card_bg
        content.config(bg=color)
        for lbl in labels: lbl.config(bg=color)

    def launch_translator(self):
        self.set_loading_state(self.interp_ui, "INITIALIZING...", "disabled_interp")
        process = subprocess.Popen([sys.executable, "app.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        threading.Thread(target=self.monitor_process, args=(process,), daemon=True).start()

    def launch_tutor(self):
        self.set_loading_state(self.tutor_ui, "LOADING DIAGNOSTICS...", "disabled_tutor")
        process = subprocess.Popen([sys.executable, "learn.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        threading.Thread(target=self.monitor_process, args=(process,), daemon=True).start()

    def launch_admin(self):
        self.set_loading_state(self.admin_ui, "VERIFYING CLEARANCE...", "disabled_admin")
        process = subprocess.Popen([sys.executable, "admin.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        threading.Thread(target=self.monitor_process, args=(process,), daemon=True).start()

    def set_loading_state(self, ui_elements, text, disabled_name):
        card, content, labels, _ = ui_elements
        card.winfo_name = lambda: disabled_name 
        self.btn_quit.config(state="disabled", cursor="watch")
        
        for lbl in self.nav_labels.values():
            lbl.config(cursor="watch")
            lbl.unbind("<Button-1>")

        content.config(bg=self.accent_warn, cursor="watch")
        for lbl in labels: lbl.config(bg=self.accent_warn, cursor="watch")
        
        # Ensure the hourglass gets the same leading space to stay centered
        labels[0].config(text=" ⏳", fg="white") 
        labels[1].config(text=text, fg="white")
        self.root.update()

    def reset_ui_state(self):
        self.switch_view("Dashboard", self.render_dashboard)
        self.btn_quit.config(state="normal", cursor="hand2")
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(50, lambda: self.root.attributes('-topmost', False))
        self.root.focus_force()

    def monitor_process(self, process):
        for line in iter(process.stdout.readline, ''):
            sys.stdout.write(line) 
            sys.stdout.flush()
            if "[GUI_READY]" in line: self.root.after(0, self.root.withdraw) 
        process.wait()
        self.root.after(0, self.reset_ui_state)

if __name__ == "__main__":
    app = SignLinkApp()
    app.root.mainloop()