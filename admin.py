import tkinter as tk
from tkinter import ttk, font, messagebox
import sqlite3

class AdminDashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SignLink - Administrator Control Center")
        
        # Enterprise Dark Palette
        self.bg_color = "#0f172a"
        self.card_bg = "#1e293b"
        self.text_primary = "#ffffff"
        self.text_secondary = "#94a3b8"
        self.accent_blue = "#3b82f6"
        self.accent_green = "#10b981"
        self.accent_red = "#ef4444"
        self.accent_red_hover = "#dc2626"

        self.root.geometry("1000x650")
        self.root.configure(bg=self.bg_color)
        
        # OS Focus Force
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(50, lambda: self.root.attributes('-topmost', False))
        self.root.focus_force()

        self.build_ui()
        self.refresh_data()

    def build_ui(self):
        # --- HEADER ---
        header = tk.Frame(self.root, bg="#020617", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="🛡️ SYSTEM ADMINISTRATOR PANEL", font=("Segoe UI", 16, "bold"), bg="#020617", fg=self.accent_red).pack(side="left", padx=20, pady=15)
        
        # Refresh Button in Header
        tk.Button(header, text="↻ Refresh Data", font=("Segoe UI", 10, "bold"), bg=self.accent_blue, fg="white", relief="flat", cursor="hand2", command=self.refresh_data).pack(side="right", padx=20, pady=15)

        # --- SPLIT SCREEN LAYOUT ---
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ---> FORCED CLAM THEME FIX (To ensure text is always visible) <---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=self.card_bg, foreground="#ffffff", fieldbackground=self.card_bg, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#020617", foreground=self.text_secondary, font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map('Treeview', background=[('selected', self.accent_blue)], foreground=[('selected', '#ffffff')])

        # ==========================================
        # LEFT CARD: USER MANAGEMENT
        # ==========================================
        left_card = tk.Frame(main_frame, bg=self.card_bg)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(left_card, text="User Management", font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=self.text_primary).pack(pady=10)
        
        columns_users = ("ID", "Username", "Role", "Progress")
        self.tree_users = ttk.Treeview(left_card, columns=columns_users, show="headings", height=15)
        for col in columns_users:
            self.tree_users.heading(col, text=col)
            self.tree_users.column(col, anchor="center", width=80)
        self.tree_users.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # User Action Buttons
        user_action_frame = tk.Frame(left_card, bg=self.card_bg)
        user_action_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        btn_style = {"font": ("Segoe UI", 9, "bold"), "fg": "white", "relief": "flat", "cursor": "hand2"}
        
        # New "Promote to Admin" Button!
        tk.Button(user_action_frame, text="👑 Promote to Admin", bg=self.accent_green, activebackground="#059669", command=self.promote_user, **btn_style).pack(side="left", expand=True, fill="x", padx=2, ipady=3)
        tk.Button(user_action_frame, text="🗑️ Delete User", bg=self.accent_red, activebackground=self.accent_red_hover, command=self.delete_user, **btn_style).pack(side="left", expand=True, fill="x", padx=2, ipady=3)

        # ==========================================
        # RIGHT CARD: TRANSLATION MODERATION
        # ==========================================
        right_card = tk.Frame(main_frame, bg=self.card_bg)
        right_card.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(right_card, text="Global Translation Logs", font=("Segoe UI", 12, "bold"), bg=self.card_bg, fg=self.text_primary).pack(pady=10)
        
        columns_trans = ("Log ID", "User ID", "Translation", "Timestamp")
        self.tree_trans = ttk.Treeview(right_card, columns=columns_trans, show="headings", height=15)
        for col in columns_trans:
            self.tree_trans.heading(col, text=col)
        self.tree_trans.column("Log ID", anchor="center", width=60)
        self.tree_trans.column("User ID", anchor="center", width=60)
        self.tree_trans.column("Translation", anchor="w", width=200)
        self.tree_trans.column("Timestamp", anchor="center", width=140)
        self.tree_trans.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Translation Action Buttons
        trans_action_frame = tk.Frame(right_card, bg=self.card_bg)
        trans_action_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        tk.Button(trans_action_frame, text="🗑️ Delete Selected Log", font=("Segoe UI", 10, "bold"), bg=self.accent_red, fg="white", activebackground=self.accent_red_hover, relief="flat", cursor="hand2", command=self.delete_translation).pack(fill="x", ipady=3)

        # --- FOOTER ---
        btn_close = tk.Button(self.root, text="CLOSE ADMIN PANEL", font=("Segoe UI", 10, "bold"), bg="#475569", fg="white", activebackground="#334155", relief="flat", cursor="hand2", command=self.root.destroy)
        btn_close.pack(pady=(0, 20), ipadx=30, ipady=5)

    # ==========================================
    # DATABASE READ OPERATIONS
    # ==========================================
    def refresh_data(self):
        for item in self.tree_users.get_children():
            self.tree_users.delete(item)
        for item in self.tree_trans.get_children():
            self.tree_trans.delete(item)
            
        self.fetch_users()
        self.fetch_translations()

    def fetch_users(self):
        try:
            conn = sqlite3.connect('signlink.db')
            c = conn.cursor()
            c.execute("""
                SELECT u.id, u.username, u.role, IFNULL(p.current_index, 0) 
                FROM users u 
                LEFT JOIN progress p ON u.id = p.user_id
            """)
            for row in c.fetchall():
                self.tree_users.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch users: {e}")

    def fetch_translations(self):
        try:
            conn = sqlite3.connect('signlink.db')
            c = conn.cursor()
            c.execute("SELECT id, user_id, text, timestamp FROM translations ORDER BY timestamp DESC")
            for row in c.fetchall():
                self.tree_trans.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to fetch translations: {e}")

    # ==========================================
    # DATABASE WRITE/DELETE OPERATIONS
    # ==========================================
    def promote_user(self):
        """Grants Admin privileges to a standard User."""
        selected_item = self.tree_users.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a user to promote.")
            return
            
        user_data = self.tree_users.item(selected_item[0])['values']
        user_id = user_data[0]
        username = user_data[1]
        role = user_data[2]

        if role == "Admin":
            messagebox.showinfo("Already Admin", f"'{username}' is already an Administrator.")
            return

        confirm = messagebox.askyesno("Confirm Promotion", f"Are you sure you want to promote '{username}' to an Admin?\n\nThey will gain full access to the Control Center.")
        if confirm:
            try:
                conn = sqlite3.connect('signlink.db')
                c = conn.cursor()
                c.execute("UPDATE users SET role='Admin' WHERE id=?", (user_id,))
                conn.commit()
                conn.close()
                self.refresh_data()
                messagebox.showinfo("Success", f"User '{username}' is now an Administrator.")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to promote user: {e}")

    def delete_user(self):
        selected_item = self.tree_users.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a user to delete.")
            return
            
        user_data = self.tree_users.item(selected_item[0])['values']
        user_id = user_data[0]
        username = user_data[1]
        role = user_data[2]

        if role == "Admin":
            messagebox.showerror("Permission Denied", "You cannot delete an Administrator account.")
            return

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete '{username}'?\n\nThis will also wipe all of their learning progress and translation logs.")
        
        if confirm:
            try:
                conn = sqlite3.connect('signlink.db')
                c = conn.cursor()
                c.execute("DELETE FROM users WHERE id=?", (user_id,))
                c.execute("DELETE FROM progress WHERE user_id=?", (user_id,))
                c.execute("DELETE FROM translations WHERE user_id=?", (user_id,))
                conn.commit()
                conn.close()
                self.refresh_data()
                messagebox.showinfo("Success", f"User '{username}' and all associated data have been purged.")
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete user: {e}")

    def delete_translation(self):
        selected_item = self.tree_trans.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a translation log to delete.")
            return
            
        log_data = self.tree_trans.item(selected_item[0])['values']
        log_id = log_data[0]
        translation_text = log_data[2]

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete this log?\n\n'{translation_text}'")
        
        if confirm:
            try:
                conn = sqlite3.connect('signlink.db')
                c = conn.cursor()
                c.execute("DELETE FROM translations WHERE id=?", (log_id,))
                conn.commit()
                conn.close()
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to delete log: {e}")

if __name__ == "__main__":
    app = AdminDashboard()
    print("[GUI_READY]", flush=True) 
    app.root.mainloop()