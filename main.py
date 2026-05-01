import tkinter as tk
from tkinter import font, ttk, messagebox
import subprocess
import sys
import threading
import sqlite3
import bcrypt
import secrets
import json
import os

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
        self.btn_font = font.Font(family="Segoe UI", size=12, weight="bold")

        self.current_user_id = None
        self.current_username = None
        self.current_role = None

        self.init_database()
        self.center_window()
        
        if self.validate_existing_session():
            self.build_dashboard_ui()
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
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT, session_token TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS progress 
                     (user_id INTEGER PRIMARY KEY, current_index INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS translations 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, text TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

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
            c.execute("SELECT username, role FROM users WHERE id=? AND session_token=?", (stored_id, stored_token))
            user = c.fetchone()
            conn.close()
            
            if user:
                self.current_user_id = stored_id
                self.current_username = user[0]
                self.current_role = user[1]
                return True
            return False
        except: return False

    def build_auth_ui(self):
        for widget in self.root.winfo_children(): widget.destroy()
        self.root.title("SignLink - Secure Access")
        
        sidebar = tk.Frame(self.root, bg=self.sidebar_bg, width=350)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="🤟 SignLink", font=self.logo_font, bg=self.sidebar_bg, fg=self.text_primary).pack(pady=(180, 10))
        tk.Label(sidebar, text="Secure Enterprise Access", font=self.normal_font, bg=self.sidebar_bg, fg=self.accent_blue).pack()
        
        self.auth_frame = tk.Frame(self.root, bg=self.main_bg)
        self.auth_frame.pack(side="right", fill="both", expand=True)
        self.show_login_frame()

    def show_login_frame(self):
        for widget in self.auth_frame.winfo_children(): widget.destroy()
        container = tk.Frame(self.auth_frame, bg=self.main_bg)
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(container, text="System Login", font=self.header_font, bg=self.main_bg, fg=self.text_primary).pack(pady=(0, 20))
        tk.Label(container, text="Username", font=self.normal_font, bg=self.main_bg, fg=self.text_secondary).pack(anchor="w")
        self.entry_login_user = tk.Entry(container, font=self.normal_font, bg=self.card_bg, fg=self.text_primary, insertbackground="white", relief="flat")
        self.entry_login_user.pack(fill="x", pady=(5, 15), ipady=5)
        tk.Label(container, text="Password", font=self.normal_font, bg=self.main_bg, fg=self.text_secondary).pack(anchor="w")
        
        pw_frame = tk.Frame(container, bg=self.main_bg)
        pw_frame.pack(fill="x", pady=(5, 25))
        self.entry_login_pass = tk.Entry(pw_frame, font=self.normal_font, bg=self.card_bg, fg=self.text_primary, insertbackground="white", relief="flat", show="●")
        self.entry_login_pass.pack(side="left", fill="x", expand=True, ipady=5)
        self.btn_show_login = tk.Button(pw_frame, text="👁", font=self.normal_font, bg=self.card_bg, fg=self.text_secondary, relief="flat", cursor="hand2", command=lambda: self.toggle_password(self.entry_login_pass, self.btn_show_login))
        self.btn_show_login.pack(side="right", padx=(5, 0), ipady=1)

        tk.Button(container, text="AUTHENTICATE", font=self.btn_font, bg=self.accent_blue, fg="white", activebackground=self.accent_blue_hover, relief="flat", cursor="hand2", command=self.process_login).pack(fill="x", ipady=5)
        tk.Button(container, text="Create a new account", font=self.normal_font, bg=self.main_bg, fg=self.accent_green, activebackground=self.main_bg, activeforeground="white", relief="flat", cursor="hand2", command=self.show_register_frame).pack(pady=15)

    def show_register_frame(self):
        for widget in self.auth_frame.winfo_children(): widget.destroy()
        container = tk.Frame(self.auth_frame, bg=self.main_bg)
        container.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(container, text="Register Profile", font=self.header_font, bg=self.main_bg, fg=self.text_primary).pack(pady=(0, 20))
        tk.Label(container, text="Choose Username", font=self.normal_font, bg=self.main_bg, fg=self.text_secondary).pack(anchor="w")
        self.entry_reg_user = tk.Entry(container, font=self.normal_font, bg=self.card_bg, fg=self.text_primary, insertbackground="white", relief="flat")
        self.entry_reg_user.pack(fill="x", pady=(5, 15), ipady=5)
        tk.Label(container, text="Choose Password (Min 6 chars)", font=self.normal_font, bg=self.main_bg, fg=self.text_secondary).pack(anchor="w")
        
        pw_frame = tk.Frame(container, bg=self.main_bg)
        pw_frame.pack(fill="x", pady=(5, 25))
        self.entry_reg_pass = tk.Entry(pw_frame, font=self.normal_font, bg=self.card_bg, fg=self.text_primary, insertbackground="white", relief="flat", show="●")
        self.entry_reg_pass.pack(side="left", fill="x", expand=True, ipady=5)
        self.btn_show_reg = tk.Button(pw_frame, text="👁", font=self.normal_font, bg=self.card_bg, fg=self.text_secondary, relief="flat", cursor="hand2", command=lambda: self.toggle_password(self.entry_reg_pass, self.btn_show_reg))
        self.btn_show_reg.pack(side="right", padx=(5, 0), ipady=1)

        tk.Button(container, text="REGISTER & LOGIN", font=self.btn_font, bg=self.accent_green, fg="white", activebackground="#059669", relief="flat", cursor="hand2", command=self.process_register).pack(fill="x", ipady=5)
        tk.Button(container, text="Back to Login", font=self.normal_font, bg=self.main_bg, fg=self.accent_blue, activebackground=self.main_bg, activeforeground="white", relief="flat", cursor="hand2", command=self.show_login_frame).pack(pady=15)

    def toggle_password(self, entry_widget, btn_widget):
        if entry_widget.cget('show') == '':
            entry_widget.config(show='●')
            btn_widget.config(fg=self.text_secondary)
        else:
            entry_widget.config(show='')
            btn_widget.config(fg=self.accent_blue)

    def process_login(self):
        username = self.entry_login_user.get().strip()
        password = self.entry_login_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Validation Error", "All fields are required.")
            return

        conn = sqlite3.connect('signlink.db')
        c = conn.cursor()
        c.execute("SELECT id, username, password, role FROM users WHERE username=?", (username,))
        user = c.fetchone()
        
        if user and self.check_password(password, user[2]):
            self.current_user_id = user[0]
            self.current_username = user[1]
            self.current_role = user[3]
            
            new_token = self.generate_session_token()
            c.execute("UPDATE users SET session_token=? WHERE id=?", (new_token, self.current_user_id))
            conn.commit()
            
            self.create_session_file(new_token)
            self.build_dashboard_ui()
        else:
            messagebox.showerror("Access Denied", "Invalid username or password.")
        conn.close()

    def process_register(self):
        username = self.entry_reg_user.get().strip()
        password = self.entry_reg_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Validation Error", "All fields are required.")
            return
        if len(password) < 6:
            messagebox.showwarning("Weak Password", "Password must be at least 6 characters long.")
            return

        hashed_pw = self.hash_password(password)
        new_token = self.generate_session_token()

        conn = sqlite3.connect('signlink.db')
        c = conn.cursor()
        
        try:
            c.execute("SELECT COUNT(*) FROM users")
            user_count = c.fetchone()[0]
            assigned_role = "Admin" if user_count == 0 else "User"

            c.execute("INSERT INTO users (username, password, role, session_token) VALUES (?, ?, ?, ?)", 
                      (username, hashed_pw, assigned_role, new_token))
            user_id = c.lastrowid
            
            c.execute("INSERT INTO progress (user_id, current_index) VALUES (?, ?)", (user_id, 0))
            conn.commit()
            
            self.current_user_id = user_id
            self.current_username = username
            self.current_role = assigned_role
            self.create_session_file(new_token)
            self.build_dashboard_ui()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Registration Error", "Username already exists! Choose another.")
        finally:
            conn.close()

    def create_session_file(self, token):
        session_data = {"user_id": self.current_user_id, "username": self.current_username, "session_token": token}
        with open("session.json", "w") as f:
            json.dump(session_data, f)

    def logout(self):
        if self.current_user_id:
            conn = sqlite3.connect('signlink.db')
            c = conn.cursor()
            c.execute("UPDATE users SET session_token=NULL WHERE id=?", (self.current_user_id,))
            conn.commit()
            conn.close()
        if os.path.exists("session.json"):
            os.remove("session.json")
        self.current_user_id = None
        self.current_username = None
        self.current_role = None
        self.build_auth_ui()

    # ==========================================
    # 5. MAIN DASHBOARD UI
    # ==========================================
    def build_dashboard_ui(self):
        for widget in self.root.winfo_children(): widget.destroy()
        self.root.title(f"SignLink - Logged in as {self.current_username}")

        sidebar = tk.Frame(self.root, bg=self.sidebar_bg, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False) 

        tk.Label(sidebar, text="🤟 SignLink", font=self.logo_font, bg=self.sidebar_bg, fg=self.text_primary).pack(pady=(40, 5), anchor="center")
        tk.Label(sidebar, text="B.Tech Major Project", font=self.normal_font, bg=self.sidebar_bg, fg=self.accent_blue).pack(anchor="center")
        
        tk.Frame(sidebar, bg=self.card_bg, height=1).pack(fill="x", padx=20, pady=25)

        tk.Label(sidebar, text=f"Active Session:", font=("Segoe UI", 9), bg=self.sidebar_bg, fg=self.text_secondary).pack(anchor="w", padx=25)
        
        role_color = self.accent_red if self.current_role == "Admin" else self.accent_green
        tk.Label(sidebar, text=f"{self.current_username} [{self.current_role}]", font=font.Font(family="Segoe UI", size=14, weight="bold"), bg=self.sidebar_bg, fg=role_color).pack(anchor="w", padx=25, pady=(0, 15))

        self.btn_quit = tk.Button(
            sidebar, text="⏻ SECURE LOGOUT", font=font.Font(family="Segoe UI", size=10, weight="bold"),
            bg=self.sidebar_bg, fg=self.accent_red, activebackground=self.accent_red_hover, activeforeground="white",
            relief="flat", cursor="hand2", command=self.logout, pady=10
        )
        self.btn_quit.pack(side="bottom", fill="x", pady=20, padx=20)
        self.btn_quit.bind("<Enter>", lambda e: self.btn_quit.config(bg=self.accent_red, fg="white") if self.btn_quit['state'] == 'normal' else None)
        self.btn_quit.bind("<Leave>", lambda e: self.btn_quit.config(bg=self.sidebar_bg, fg=self.accent_red) if self.btn_quit['state'] == 'normal' else None)

        main_area = tk.Frame(self.root, bg=self.main_bg)
        main_area.pack(side="left", fill="both", expand=True)

        # ---> ROLE SEPARATION LOGIC <---
        if self.current_role == "Admin":
            tk.Label(main_area, text="System Administration", font=self.header_font, bg=self.main_bg, fg=self.text_primary).pack(anchor="w", padx=40, pady=(40, 20))
            self.card_admin, self.lbl_admin_title = self.create_module_card(
                parent=main_area, icon="🛡️", title="Administrator Dashboard",
                description="Manage user accounts, promote admins, and view global logs.",
                accent_color=self.accent_red, command=self.launch_admin
            )
        else:
            tk.Label(main_area, text="Module Selection", font=self.header_font, bg=self.main_bg, fg=self.text_primary).pack(anchor="w", padx=40, pady=(40, 20))
            self.card_interpreter, self.lbl_interp_title = self.create_module_card(
                parent=main_area, icon="🌐", title="Sign Language Interpreter",
                description="Translations are securely logged to your encrypted profile.",
                accent_color=self.accent_green, command=self.launch_translator
            )
            self.card_tutor, self.lbl_tutor_title = self.create_module_card(
                parent=main_area, icon="🧠", title="Interactive Learning Curriculum",
                description="Your learning matrices are actively synced to the database.",
                accent_color=self.accent_blue, command=self.launch_tutor
            )

    def create_module_card(self, parent, icon, title, description, accent_color, command):
        container = tk.Frame(parent, bg=self.main_bg)
        container.pack(fill="x", padx=40, pady=5)
        card = tk.Frame(container, bg=self.card_bg, cursor="hand2")
        card.pack(fill="x")
        tk.Frame(card, bg=accent_color, width=4).pack(side="left", fill="y")
        content = tk.Frame(card, bg=self.card_bg, padx=20, pady=15, cursor="hand2")
        content.pack(side="left", fill="both", expand=True)
        lbl_title = tk.Label(content, text=f"{icon}   {title}", font=font.Font(family="Segoe UI", size=14, weight="bold"), bg=self.card_bg, fg=self.text_primary, cursor="hand2")
        lbl_title.pack(anchor="w")
        lbl_desc = tk.Label(content, text=description, font=self.normal_font, bg=self.card_bg, fg=self.text_secondary, cursor="hand2")
        lbl_desc.pack(anchor="w", pady=(2, 0))

        elements = [card, content, lbl_title, lbl_desc]
        for el in elements:
            el.bind("<Button-1>", lambda e: command() if card.winfo_name() not in ["disabled_interp", "disabled_tutor", "disabled_admin"] else None)
            el.bind("<Enter>", lambda e, c=card, ct=content, t=lbl_title, d=lbl_desc: self.on_card_hover(c, ct, t, d, True))
            el.bind("<Leave>", lambda e, c=card, ct=content, t=lbl_title, d=lbl_desc: self.on_card_hover(c, ct, t, d, False))
        return card, lbl_title

    def on_card_hover(self, card, content, title, desc, is_hovering):
        if card.winfo_name() in ["disabled_interp", "disabled_tutor", "disabled_admin"]: return 
        color = self.card_hover if is_hovering else self.card_bg
        card.config(bg=color)
        content.config(bg=color)
        title.config(bg=color)
        desc.config(bg=color)

    def launch_translator(self):
        self.set_loading_state(self.card_interpreter, self.lbl_interp_title, "INITIALIZING AI ENGINE...", "disabled_interp")
        process = subprocess.Popen([sys.executable, "app.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        threading.Thread(target=self.monitor_process, args=(process,), daemon=True).start()

    def launch_tutor(self):
        self.set_loading_state(self.card_tutor, self.lbl_tutor_title, "LOADING DIAGNOSTICS...", "disabled_tutor")
        process = subprocess.Popen([sys.executable, "learn.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        threading.Thread(target=self.monitor_process, args=(process,), daemon=True).start()

    def launch_admin(self):
        self.set_loading_state(self.card_admin, self.lbl_admin_title, "VERIFYING CLEARANCE...", "disabled_admin")
        process = subprocess.Popen([sys.executable, "admin.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        threading.Thread(target=self.monitor_process, args=(process,), daemon=True).start()

    def set_loading_state(self, active_card, title_label, text, disabled_name):
        active_card.winfo_name = lambda: disabled_name 
        self.btn_quit.config(state="disabled", cursor="watch")
        active_card.config(bg=self.accent_warn, cursor="watch")
        for child in active_card.winfo_children():
            child.config(bg=self.accent_warn, cursor="watch")
            for subchild in child.winfo_children():
                subchild.config(bg=self.accent_warn, cursor="watch")
        title_label.config(text=f"⏳   {text}", fg="white")
        self.root.update()

    def reset_ui_state(self):
        if self.current_role == "Admin":
            self.card_admin.winfo_name = lambda: "active"
            self.on_card_hover(self.card_admin, self.card_admin.winfo_children()[1], self.lbl_admin_title, self.card_admin.winfo_children()[1].winfo_children()[1], False)
            self.lbl_admin_title.config(text="🛡️   Administrator Dashboard", fg=self.text_primary)
        else:
            self.card_interpreter.winfo_name = lambda: "active"
            self.on_card_hover(self.card_interpreter, self.card_interpreter.winfo_children()[1], self.lbl_interp_title, self.card_interpreter.winfo_children()[1].winfo_children()[1], False)
            self.lbl_interp_title.config(text="🌐   Sign Language Interpreter", fg=self.text_primary)
            
            self.card_tutor.winfo_name = lambda: "active"
            self.on_card_hover(self.card_tutor, self.card_tutor.winfo_children()[1], self.lbl_tutor_title, self.card_tutor.winfo_children()[1].winfo_children()[1], False)
            self.lbl_tutor_title.config(text="🧠   Interactive Learning Curriculum", fg=self.text_primary)

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
            if "[GUI_READY]" in line:
                self.root.after(0, self.root.withdraw) 
        process.wait()
        self.root.after(0, self.reset_ui_state)

if __name__ == "__main__":
    app = SignLinkApp()
    app.root.mainloop()