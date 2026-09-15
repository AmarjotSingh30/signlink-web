from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, ttk
import cv2
import os
import numpy as np
from keras.models import model_from_json
import mediapipe as mp
import pyttsx3
import threading
import sqlite3
import json
from datetime import datetime

class Application:
    def __init__(self):
        self.directory = 'model/' 
        
        # Initialize Camera
        self.vs = cv2.VideoCapture(0)
        self.current_image = None
        self.current_image2 = None
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Load the Dense Neural Network
        print("Loading Dense Neural Network...")
        self.json_file = open(self.directory+"model-mp.json", "r")
        self.model_json = self.json_file.read()
        self.json_file.close()
        self.loaded_model = model_from_json(self.model_json)
        self.loaded_model.load_weights(self.directory+"model-mp.h5")
        
        raw_classes = np.load(self.directory+'classes.npy', allow_pickle=True)
        self.classes = [str(c) for c in raw_classes]
        
        self.excluded_signs = ['BLANK', 'DEL', 'DELETE', 'SPACE', 'NOTHING']

        self.str = ""
        self.current_symbol = "--"
        
        self.vocab = [
            "ABOUT", "AFTER", "AGAIN", "ALL", "ALWAYS", "AND", "ANY", "ARE", "ASK", "BAD", "BECAUSE", "BEFORE", "BEST", "BETTER", "BIG", 
            "BOOK", "BOY", "BROTHER", "BUT", "CALL", "CAN", "CAR", "CAT", "CITY", "COLD", "COME", "COULD", "DAY", "DEAF", "DO", "DOG", 
            "DONE", "DOWN", "DRINK", "EAT", "EVERY", "FAMILY", "FATHER", "FEEL", "FIND", "FINE", "FIRST", "FOOD", "FOR", "FRIEND", "FROM", 
            "GIRL", "GIVE", "GO", "GOOD", "GREAT", "HAPPY", "HAVE", "HE", "HEARING", "HELLO", "HELP", "HER", "HERE", "HIM", "HIS", "HOME", 
            "HOT", "HOW", "I", "IF", "IN", "IS", "IT", "JUST", "KNOW", "LEARN", "LIKE", "LITTLE", "LOVE", "MAKE", "MAN", "MANY", "ME", 
            "MORE", "MORNING", "MOTHER", "MY", "NAME", "NEED", "NEW", "NIGHT", "NO", "NOT", "NOW", "OF", "OKAY", "ONE", "ONLY", "OR", 
            "OTHER", "OUR", "OUT", "OVER", "PEOPLE", "PLAY", "PLEASE", "READ", "RIGHT", "SAD", "SAME", "SAY", "SCHOOL", "SEE", "SHE", 
            "SISTER", "SOME", "SORRY", "STOP", "TAKE", "TELL", "THANK", "THAT", "THE", "THEIR", "THEM", "THEN", "THERE", "THESE", "THEY", 
            "THING", "THINK", "THIS", "TIME", "TO", "TODAY", "TOMORROW", "TOO", "UNDERSTAND", "UP", "US", "USE", "VERY", "WANT", "WAS", 
            "WATER", "WAY", "WE", "WELL", "WENT", "WERE", "WHAT", "WHEN", "WHERE", "WHICH", "WHO", "WHY", "WILL", "WITH", "WORK", "WORLD", 
            "WOULD", "YEAR", "YES", "YOU", "YOUR"
        ]

        # ---> LOAD USER SESSION <---
        self.current_user_id = None
        self.current_username = "Guest"
        if os.path.exists("session.json"):
            try:
                with open("session.json", "r") as f:
                    data = json.load(f)
                    self.current_user_id = data.get("user_id")
                    self.current_username = data.get("username", "Guest")
            except Exception as e:
                print(f"[SYSTEM ERROR] Could not load session data: {e}")
        
        # ==========================================
        # FULLY RESPONSIVE ENTERPRISE GUI
        # ==========================================
        self.root = tk.Tk()
        self.root.title(f"SignLink Interpreter - Authenticated as {self.current_username}")
        self.root.protocol('WM_DELETE_WINDOW', self.destructor)
        self.root.geometry("900x700") 
        self.root.minsize(800, 600) 
        
        self.BG_COLOR = "#0f172a"       
        self.CARD_BG = "#1e293b"        
        self.HEADER_BG = "#020617"      
        self.TEXT_PRIMARY = "#ffffff"   
        self.TEXT_MUTED = "#94a3b8"
        self.ACCENT_BLUE = "#2563eb"
        self.BTN_WARN = "#d97706"
        self.BTN_DANGER = "#dc2626"
        self.BTN_SUCCESS = "#059669"
        self.BORDER_COLOR = "#334155"
        
        self.root.configure(bg=self.BG_COLOR) 
        
        header_frame = tk.Frame(self.root, bg=self.HEADER_BG, height=50)
        header_frame.place(relx=0, rely=0, relwidth=1)
        tk.Label(header_frame, text="SIGN LANGUAGE INTERPRETER", 
                 font=("Segoe UI", 16, "bold"), bg=self.HEADER_BG, fg=self.ACCENT_BLUE).place(x=20, y=10)

        cam_frame = tk.Frame(self.root, bg=self.CARD_BG, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        cam_frame.place(relx=0.02, rely=0.09, relwidth=0.56, relheight=0.48)
        tk.Label(cam_frame, text="Live Video Feed", font=("Segoe UI", 11, "bold"), bg=self.CARD_BG, fg=self.TEXT_PRIMARY).place(x=20, y=10)
        
        self.panel = tk.Label(cam_frame, bg="#000000")
        self.panel.place(relx=0.04, rely=0.15, relwidth=0.92, relheight=0.80) 
        
        skel_frame = tk.Frame(self.root, bg=self.CARD_BG, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        skel_frame.place(relx=0.60, rely=0.09, relwidth=0.38, relheight=0.48)
        tk.Label(skel_frame, text="Handlandmarks Preview", font=("Segoe UI", 11, "bold"), bg=self.CARD_BG, fg=self.TEXT_PRIMARY).place(x=20, y=10)
        
        self.panel2 = tk.Label(skel_frame, bg="#000000") 
        self.panel2.place(relx=0.1, rely=0.15, relwidth=0.8, relheight=0.80) 
        
        self.char_var = tk.StringVar(value="--")

        sugg_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        sugg_frame.place(relx=0.02, rely=0.59, relwidth=0.96, relheight=0.05)
        
        self.suggestion_btns = []
        for i in range(3):
            btn = tk.Button(sugg_frame, text="", font=("Segoe UI", 12, "bold"), bg=self.CARD_BG, fg=self.ACCENT_BLUE, 
                            activebackground=self.BORDER_COLOR, activeforeground="white", relief="flat", cursor="hand2",
                            command=lambda idx=i: self.apply_suggestion(idx))
            btn.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
            self.suggestion_btns.append(btn)

        # BUTTON CONTAINER
        btn_container = tk.Frame(self.root, bg=self.BG_COLOR)
        btn_container.place(relx=0.02, rely=0.66, relwidth=0.96, relheight=0.06)
        
        btn_style = {"font": ("Segoe UI", 9, "bold"), "fg": "white", "relief": "flat", "cursor": "hand2"}
        
        self.btn_space = tk.Button(btn_container, text="Space/Speak", bg=self.ACCENT_BLUE, activebackground="#1d4ed8", command=self.add_space, **btn_style)
        self.btn_space.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=3)

        self.btn_backspace = tk.Button(btn_container, text="Backspace", bg=self.BTN_WARN, activebackground="#b45309", command=self.backspace, **btn_style)
        self.btn_backspace.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=3)

        self.btn_clear_all = tk.Button(btn_container, text="Clear", bg=self.BTN_DANGER, activebackground="#991b1b", command=self.clear_all, **btn_style)
        self.btn_clear_all.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=3)

        self.btn_save = tk.Button(btn_container, text="Export & Save", bg=self.BTN_SUCCESS, activebackground="#047857", command=self.export_and_save, **btn_style)
        self.btn_save.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=3)
        
        self.btn_history = tk.Button(btn_container, text="View History", bg="#6366f1", activebackground="#4f46e5", command=self.view_history, **btn_style)
        self.btn_history.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=3)

        self.btn_quit = tk.Button(btn_container, text="Terminate", bg="#475569", activebackground="#334155", command=self.destructor, **btn_style)
        self.btn_quit.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=3)

        # OUTPUT CONSOLE
        out_frame = tk.Frame(self.root, bg=self.CARD_BG, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        out_frame.place(relx=0.02, rely=0.74, relwidth=0.96, relheight=0.23)
        
        tk.Label(out_frame, text="Translation Console", font=("Segoe UI", 12, "bold"), bg=self.CARD_BG, fg=self.TEXT_PRIMARY).place(x=20, y=5)
        
        tk.Label(out_frame, text="Detected Sign:", font=("Segoe UI", 12), bg=self.CARD_BG, fg=self.TEXT_MUTED).place(relx=0.38, y=15)
        tk.Label(out_frame, textvariable=self.char_var, font=("Segoe UI", 24, "bold"), bg=self.CARD_BG, fg=self.BTN_SUCCESS).place(relx=0.52, y=5)
        
        self.sentence_box = tk.Text(out_frame, font=("Consolas", 16), bg="#020617", fg="#10b981", insertbackground="#020617",
                                    relief="flat", highlightbackground=self.BORDER_COLOR, highlightthickness=1, wrap="word", padx=10, pady=10)
        self.sentence_box.place(relx=0.02, rely=0.40, relwidth=0.96, relheight=0.50)
        
        # ---> ANTI-COPY / FEATURE ENFORCEMENT LOCK <---
        self.sentence_box.config(state=tk.DISABLED)
        self.sentence_box.bind("<Button-1>", lambda e: "break")       
        self.sentence_box.bind("<B1-Motion>", lambda e: "break")      
        self.sentence_box.bind("<Control-c>", lambda e: "break")      
        self.sentence_box.bind("<Control-C>", lambda e: "break")      
        
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(50, lambda: self.root.attributes('-topmost', False))
        self.root.focus_force()
        
        self.video_loop()

    # ==========================================
    # USER ORIENTED FEATURES (HISTORY, EDIT, DELETE)
    # ==========================================
    def view_history(self):
        """A custom built Workspace using native widgets immune to Theme Bugs."""
        if not self.current_user_id:
            messagebox.showinfo("Guest Mode", "Translation history is only available for registered users.")
            return

        history_win = tk.Toplevel(self.root)
        history_win.title(f"{self.current_username}'s Translation Workspace")
        history_win.geometry("850x500")
        history_win.configure(bg=self.BG_COLOR)

        history_win.lift()
        history_win.attributes('-topmost', True)
        history_win.after(50, lambda: history_win.attributes('-topmost', False))
        history_win.focus_force()

        tk.Label(history_win, text="📖 Your Translation Workspace", font=("Segoe UI", 16, "bold"), bg=self.BG_COLOR, fg=self.ACCENT_BLUE).pack(pady=10)

        # Bulletproof Native Listbox Container
        list_frame = tk.Frame(history_win, bg=self.CARD_BG, bd=0)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        
        # This Native Listbox will ALWAYS respect the colors we tell it
        self.history_listbox = tk.Listbox(
            list_frame, 
            bg=self.CARD_BG, 
            fg="#ffffff", 
            selectbackground=self.ACCENT_BLUE, 
            selectforeground="#ffffff",
            font=("Consolas", 12), 
            borderwidth=0, 
            highlightthickness=1,
            highlightbackground=self.BORDER_COLOR,
            yscrollcommand=scrollbar.set
        )
        
        scrollbar.config(command=self.history_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.history_listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.history_mapping = {} # Secretly maps Listbox row to Database ID

        def refresh_listbox():
            self.history_listbox.delete(0, tk.END)
            self.history_mapping.clear()
            try:
                conn = sqlite3.connect('signlink.db')
                c = conn.cursor()
                c.execute("SELECT id, timestamp, text FROM translations WHERE user_id=? ORDER BY timestamp DESC", (self.current_user_id,))
                rows = c.fetchall()
                
                if not rows:
                    self.history_listbox.insert(tk.END, " No saved translations found. Type something and click 'Export & Save'!")
                    self.history_listbox.itemconfig(0, {'fg': self.BTN_WARN})
                else:
                    for index, row in enumerate(rows):
                        db_id, timestamp, text = row[0], row[1], row[2]
                        self.history_mapping[index] = db_id
                        # Format the text cleanly
                        display_str = f" [{timestamp}]   ▶   {text}"
                        self.history_listbox.insert(tk.END, display_str)
                conn.close()
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not fetch history: {e}")

        refresh_listbox()

        # ---> THE NEW ACTION BUTTONS PANEL <---
        action_frame = tk.Frame(history_win, bg=self.BG_COLOR)
        action_frame.pack(fill="x", padx=20, pady=(0, 20))

        def load_to_console():
            selection = self.history_listbox.curselection()
            if not selection:
                messagebox.showwarning("Selection Required", "Please click on a translation to edit.", parent=history_win)
                return
            index = selection[0]
            if index not in self.history_mapping: return # Selected the empty placeholder
            
            full_text = self.history_listbox.get(index)
            # Split the text from the timestamp
            saved_text = full_text.split("   ▶   ")[1]
            
            # Load into main app and close history window
            self.str = saved_text + " "
            self.update_sentence_box()
            self.update_suggestions()
            history_win.destroy()

        def delete_entry():
            selection = self.history_listbox.curselection()
            if not selection:
                messagebox.showwarning("Selection Required", "Please click on a translation to delete.", parent=history_win)
                return
            index = selection[0]
            if index not in self.history_mapping: return
            
            db_id = self.history_mapping[index]
            
            if messagebox.askyesno("Confirm Deletion", "Are you sure you want to permanently delete this translation?", parent=history_win):
                try:
                    conn = sqlite3.connect('signlink.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM translations WHERE id=?", (db_id,))
                    conn.commit()
                    conn.close()
                    refresh_listbox()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete: {e}", parent=history_win)

        btn_style = {"font": ("Segoe UI", 10, "bold"), "fg": "white", "relief": "flat", "cursor": "hand2"}

        tk.Button(action_frame, text="Load to Console (Edit)", bg=self.BTN_SUCCESS, activebackground="#047857", command=load_to_console, **btn_style).pack(side="left", expand=True, fill="x", padx=5, ipady=4)
        tk.Button(action_frame, text="Delete Entry", bg=self.BTN_DANGER, activebackground="#991b1b", command=delete_entry, **btn_style).pack(side="left", expand=True, fill="x", padx=5, ipady=4)
        tk.Button(action_frame, text="⬅ Go Back", bg="#475569", activebackground="#334155", command=history_win.destroy, **btn_style).pack(side="left", expand=True, fill="x", padx=5, ipady=4)

    def export_and_save(self):
        translation_text = self.str.strip()
        if not translation_text:
            messagebox.showwarning("Empty Console", "No translation data available to export.")
            return
            
        # Save to Database
        if self.current_user_id:
            try:
                conn = sqlite3.connect('signlink.db')
                c = conn.cursor()
                c.execute("INSERT INTO translations (user_id, text) VALUES (?, ?)", (self.current_user_id, translation_text))
                conn.commit()
                conn.close()
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to sync with local database: {e}")

        # Generate Physical Report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_content = f"--- SIGNLINK TRANSLATION REPORT ---\n"
        report_content += f"User: {self.current_username}\n"
        report_content += f"Date: {timestamp}\n"
        report_content += f"-----------------------------------\n\n"
        report_content += f"TRANSLATION OUTPUT:\n{translation_text}\n\n"
        report_content += f"-----------------------------------\n"
        report_content += f"End of Report."

        try:
            with open("Translation_Export.txt", "w") as f:
                f.write(report_content)
            messagebox.showinfo("Export Successful", "Translation saved to Database and exported to 'Translation_Export.txt'.")
            self.speak_text("Translation securely exported.")
            self.clear_all()
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to generate physical report: {e}")

    # ==========================================
    # AUDIO VOICEOVER LOGIC (TEXT-TO-SPEECH)
    # ==========================================
    def speak_text(self, text):
        if not text.strip(): return
        def run_speech():
            try:
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"[SYSTEM ERROR] TTS Engine failed: {e}")
        threading.Thread(target=run_speech, daemon=True).start()

    # ==========================================
    # NLP PREDICTIVE TEXT LOGIC
    # ==========================================
    def update_suggestions(self):
        words = self.str.split(' ')
        current_word = words[-1].upper()
        if not current_word:
            for btn in self.suggestion_btns:
                btn.config(text="", state="disabled", bg=self.CARD_BG)
            return

        matches = [w for w in self.vocab if w.startswith(current_word) and w != current_word]
        for i in range(3):
            if i < len(matches):
                self.suggestion_btns[i].config(text=matches[i], state="normal", bg="#1e293b")
            else:
                self.suggestion_btns[i].config(text="", state="disabled", bg=self.CARD_BG)

    def apply_suggestion(self, btn_index):
        suggested_word = self.suggestion_btns[btn_index].cget("text")
        if not suggested_word: return
        words = self.str.split(' ')
        words[-1] = suggested_word
        self.str = ' '.join(words) + " "
        self.update_sentence_box()
        self.update_suggestions()
        self.speak_text(suggested_word)

    # ==========================================
    # DIRECT TYPING BUTTON LOGIC
    # ==========================================
    def add_space(self):
        words = self.str.strip().split(' ')
        if words: self.speak_text(words[-1])
        self.str += " "
        self.update_sentence_box()
        self.update_suggestions()

    def backspace(self):
        if len(self.str) > 0:
            self.str = self.str[:-1] 
            self.update_sentence_box()
            self.update_suggestions()

    def clear_all(self):
        self.str = ""
        self.update_sentence_box()
        self.update_suggestions()

    def update_sentence_box(self):
        self.sentence_box.config(state=tk.NORMAL)
        self.sentence_box.delete("1.0", tk.END)
        self.sentence_box.insert(tk.END, self.str)
        self.sentence_box.see(tk.END)
        self.sentence_box.config(state=tk.DISABLED)

    # ==========================================
    # CORE PIPELINE WITH CHIRALITY FIX
    # ==========================================
    def video_loop(self):
        ok, frame = self.vs.read()
        if ok:
            frame = cv2.flip(frame, 1)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            black_canvas = np.zeros(frame.shape, dtype=np.uint8)
            
            results = self.hands.process(cv2image)
            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    hand_type = handedness.classification[0].label 
                    self.mp_drawing.draw_landmarks(black_canvas, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    coords = []
                    for lm in hand_landmarks.landmark:
                        x_val = lm.x
                        if hand_type == "Right":  
                            x_val = 1.0 - x_val  
                        coords.extend([x_val, lm.y, lm.z])
                    self.predict(coords)
            else:
                self.current_symbol = "--"
                self.process_logic()

            w1, h1 = self.panel.winfo_width(), self.panel.winfo_height()
            w2, h2 = self.panel2.winfo_width(), self.panel2.winfo_height()
            w1, h1 = max(w1, 450), max(h1, 330)
            w2, h2 = max(w2, 250), max(h2, 250)

            cv2image_resized = cv2.resize(cv2image, (w1, h1)) 
            self.current_image = Image.fromarray(cv2image_resized)
            imgtk = ImageTk.PhotoImage(image=self.current_image)
            self.panel.imgtk = imgtk
            self.panel.config(image=imgtk)
            
            black_canvas_rgb = cv2.cvtColor(black_canvas, cv2.COLOR_BGR2RGB)
            black_canvas_resized = cv2.resize(black_canvas_rgb, (w2, h2)) 
            self.current_image2 = Image.fromarray(black_canvas_resized)
            imgtk2 = ImageTk.PhotoImage(image=self.current_image2)
            self.panel2.imgtk = imgtk2
            self.panel2.config(image=imgtk2)
            
            self.char_var.set(self.current_symbol)
                
        self.root.after(10, self.video_loop)

    def predict(self, coords):
        reshaped_coords = np.array([coords])
        predictions = self.loaded_model.predict(reshaped_coords, verbose=0)
        max_index = np.argmax(predictions[0])
        
        if predictions[0][max_index] > 0.85:
            predicted_sign = str(self.classes[max_index])
            if predicted_sign.strip().upper() not in self.excluded_signs:
                self.current_symbol = predicted_sign
            else:
                self.current_symbol = "--"
        else:
            self.current_symbol = "--"
        self.process_logic()

    def process_logic(self):
        if not hasattr(self, 'last_symbol'):
            self.last_symbol = "--"
            self.stable_frames = 0
            
        if self.current_symbol == self.last_symbol:
            self.stable_frames += 1
        else:
            self.last_symbol = self.current_symbol
            self.stable_frames = 0
            
        if self.stable_frames == 6:
            if self.current_symbol != "--":
                self.str += self.current_symbol
                self.update_sentence_box()
                self.update_suggestions() 

    def destructor(self):
        print("Terminating Application Processes...")
        self.root.destroy()
        self.vs.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    print("Booting Sign Language Interface...")
    pba = Application()
    print("[GUI_READY]", flush=True) 
    pba.root.mainloop()