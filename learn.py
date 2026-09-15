from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import os
import numpy as np
import json 
import sqlite3
from keras.models import model_from_json
import mediapipe as mp

class LearnModule:
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
        print("[SYSTEM] Booting AI Diagnostic Engine...")
        try:
            with open(self.directory+"model-mp.json", "r") as json_file:
                self.loaded_model = model_from_json(json_file.read())
            self.loaded_model.load_weights(self.directory+"model-mp.h5")
            
            raw_classes = np.load(self.directory+'classes.npy', allow_pickle=True)
            self.classes = [str(c) for c in raw_classes]
            
            self.excluded_signs = ['BLANK', 'DEL', 'DELETE', 'SPACE', 'NOTHING']
            
            available_classes = []
            for c in self.classes:
                clean_name = str(c).strip().upper() 
                if clean_name not in self.excluded_signs:
                    available_classes.append(str(c)) 
            
            self.curriculum = sorted(available_classes) 

        except Exception as e:
            print(f"[ERROR] Engine load failure: {e}")
            self.classes = [chr(i) for i in range(65, 91)]
            self.curriculum = [chr(i) for i in range(65, 91)] 
            
        self.total_modules = len(self.curriculum)
        
        # ---> SQL DATABASE PROFILE LOADING <---
        self.current_user_id = None
        self.current_username = "Guest"
        
        if os.path.exists("session.json"):
            try:
                with open("session.json", "r") as f:
                    data = json.load(f)
                    self.current_user_id = data.get("user_id")
                    self.current_username = data.get("username", "Guest")
            except Exception as e:
                print(f"[WARNING] Could not load session profile: {e}")

        self.current_index = 0
        self.is_returning_user = False
        
        if self.current_user_id:
            try:
                conn = sqlite3.connect('signlink.db')
                c = conn.cursor()
                c.execute("SELECT current_index FROM progress WHERE user_id=?", (self.current_user_id,))
                row = c.fetchone()
                if row:
                    saved_index = row[0]
                    if saved_index < self.total_modules:
                        self.current_index = saved_index
                        self.is_returning_user = True
                conn.close()
            except Exception as e:
                print(f"[SYSTEM ERROR] Could not read from DB progress table: {e}")

        # Diagnostic State Variables
        self.target_letter = self.curriculum[self.current_index]
        self.hold_frames = 0
        self.required_frames = 20 
        self.last_log_state = "" 
        self.is_transitioning = False 
        
        # ==========================================
        # 3-COLUMN ENTERPRISE GUI
        # ==========================================
        self.root = tk.Tk()
        self.root.title(f"SignLink Learning Curriculum - Authenticated as {self.current_username}")
        self.root.protocol('WM_DELETE_WINDOW', self.destructor)
        
        self.root.geometry("1100x750") 
        self.root.minsize(1000, 700) 
        
        BG_COLOR = "#0f172a"       
        CARD_BG = "#1e293b"        
        HEADER_BG = "#020617"      
        TEXT_PRIMARY = "#f8fafc"
        ACCENT_BLUE = "#2563eb"
        BTN_DANGER = "#dc2626"
        BTN_SUCCESS = "#059669"
        BORDER_COLOR = "#334155"
        
        self.root.configure(bg=BG_COLOR) 
        
        header_frame = tk.Frame(self.root, bg=HEADER_BG, height=50)
        header_frame.place(relx=0, rely=0, relwidth=1)
        tk.Label(header_frame, text="LEARN SIGN LANGUAGE", 
                 font=("Segoe UI", 16, "bold"), bg=HEADER_BG, fg=ACCENT_BLUE).place(x=20, y=10)
                 
        self.progress_var = tk.StringVar(value=f"Signs: {self.target_letter} ({self.current_index + 1}/{self.total_modules})")
        self.lbl_progress = tk.Label(header_frame, textvariable=self.progress_var, font=("Segoe UI", 14, "bold"), bg=HEADER_BG, fg=TEXT_PRIMARY)
        self.lbl_progress.place(relx=0.75, y=10)

        cam_frame = tk.Frame(self.root, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        cam_frame.place(relx=0.02, rely=0.09, relwidth=0.31, relheight=0.48)
        tk.Label(cam_frame, text="1. Live Video Feed", font=("Segoe UI", 11, "bold"), bg=CARD_BG, fg=TEXT_PRIMARY).place(x=15, y=10)
        
        self.panel = tk.Label(cam_frame, bg="#000000")
        self.panel.place(relx=0.05, rely=0.15, relwidth=0.90, relheight=0.80) 

        skel_frame = tk.Frame(self.root, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        skel_frame.place(relx=0.345, rely=0.09, relwidth=0.31, relheight=0.48)
        tk.Label(skel_frame, text="Handlandmarks Preview", font=("Segoe UI", 11, "bold"), bg=CARD_BG, fg=TEXT_PRIMARY).place(x=15, y=10)
        
        self.panel2 = tk.Label(skel_frame, bg="#000000") 
        self.panel2.place(relx=0.05, rely=0.15, relwidth=0.90, relheight=0.80) 
        
        ref_frame = tk.Frame(self.root, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        ref_frame.place(relx=0.67, rely=0.09, relwidth=0.31, relheight=0.48)
        tk.Label(ref_frame, text="Sign", font=("Segoe UI", 11, "bold"), bg=CARD_BG, fg=TEXT_PRIMARY).place(x=15, y=10)
        
        self.target_var = tk.StringVar(value=f"{self.target_letter}")
        tk.Label(ref_frame, textvariable=self.target_var, font=("Segoe UI", 32, "bold"), bg=CARD_BG, fg=BTN_SUCCESS).place(relx=0.42, y=40)
        
        self.ref_panel = tk.Label(ref_frame, bg=CARD_BG) 
        self.ref_panel.place(relx=0.1, rely=0.35, relwidth=0.8, relheight=0.6) 

        btn_container = tk.Frame(self.root, bg=BG_COLOR)
        btn_container.place(relx=0.02, rely=0.59, relwidth=0.96, relheight=0.06)
        
        btn_style = {"font": ("Segoe UI", 10, "bold"), "fg": "white", "relief": "flat", "cursor": "hand2"}
        
        self.btn_prev = tk.Button(btn_container, text="◀ Previous Sign", bg="#475569", activebackground="#334155", command=self.prev_module, **btn_style)
        self.btn_prev.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)

        self.btn_next = tk.Button(btn_container, text="Skip / Next Sign ▶", bg=ACCENT_BLUE, activebackground="#1d4ed8", command=self.next_module, **btn_style)
        self.btn_next.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)

        self.btn_quit = tk.Button(btn_container, text="Exit", bg=BTN_DANGER, activebackground="#991b1b", command=self.destructor, **btn_style)
        self.btn_quit.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)

        out_frame = tk.Frame(self.root, bg=CARD_BG, highlightbackground=BORDER_COLOR, highlightthickness=1)
        out_frame.place(relx=0.02, rely=0.67, relwidth=0.96, relheight=0.30)
        
        tk.Label(out_frame, text="Diagnostic Log", font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=TEXT_PRIMARY).place(x=20, y=5)
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure("blue.Horizontal.TProgressbar", background=ACCENT_BLUE, thickness=8)
        self.hold_progress = ttk.Progressbar(out_frame, style="blue.Horizontal.TProgressbar", orient="horizontal", mode="determinate")
        self.hold_progress.place(relx=0.02, rely=0.20, relwidth=0.96)
        
        self.terminal = tk.Text(out_frame, font=("Consolas", 12), bg="#020617", fg="#10b981", insertbackground="#020617",
                                    relief="flat", highlightbackground=BORDER_COLOR, highlightthickness=1, wrap="word", padx=10, pady=5)
        self.terminal.place(relx=0.02, rely=0.35, relwidth=0.96, relheight=0.55)
        
        self.terminal.tag_config("info", foreground="#3b82f6")    
        self.terminal.tag_config("success", foreground="#10b981") 
        self.terminal.tag_config("warn", foreground="#f59e0b")    
        self.terminal.tag_config("error", foreground="#ef4444")   
        
        self.terminal.config(state=tk.DISABLED)
        
        if self.is_returning_user:
            self.log_to_terminal(f"[SYSTEM] Welcome back {self.current_username}! Syncing DB at Matrix '{self.target_letter}'.", "success")
        else:
            self.log_to_terminal(f"[SYSTEM] DB Synced. Matrix {self.target_letter} loaded. Awaiting input...", "info")
            
        self.load_reference_image()
        
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(50, lambda: self.root.attributes('-topmost', False))
        self.root.focus_force()

        self.video_loop()

    def log_to_terminal(self, message, tag="info"):
        if message == self.last_log_state: return 
        self.last_log_state = message
        self.terminal.config(state=tk.NORMAL)
        self.terminal.insert(tk.END, message + "\n", tag)
        self.terminal.see(tk.END)
        self.terminal.config(state=tk.DISABLED)

    def load_reference_image(self):
        clean_letter = str(self.target_letter).strip()
        img_path = f"F:/G12_major_project/Sign-Language-to-Text-master/dataset/asl_alphabet_test/asl_alphabet_test/{clean_letter}.jpg"
        
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                img = img.resize((200, 200), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                self.ref_panel.imgtk = imgtk 
                self.ref_panel.config(image=imgtk, text="")
            except Exception: pass
        else:
            backup_path = f"F:/G12_major_project/Sign-Language-to-Text-master/dataset/asl_alphabet_test/asl_alphabet_test/{clean_letter}_test.jpg"
            if os.path.exists(backup_path):
                img = Image.open(backup_path)
                img = img.resize((200, 200), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                self.ref_panel.imgtk = imgtk 
                self.ref_panel.config(image=imgtk, text="")
            else:
                self.ref_panel.config(image='', text=f"[Matrix '{clean_letter}' Unavailable]", font=("Segoe UI", 12), fg="#94a3b8")

    def update_curriculum_ui(self):
        self.is_transitioning = False 
        self.target_letter = self.curriculum[self.current_index]
        self.target_var.set(f"{self.target_letter}")
        
        self.progress_var.set(f"Current Sign: {self.target_letter} ({self.current_index + 1}/{self.total_modules})")
        
        self.hold_frames = 0
        self.hold_progress['value'] = 0
        self.load_reference_image()
        
        self.terminal.config(state=tk.NORMAL)
        self.terminal.delete("1.0", tk.END)
        self.terminal.config(state=tk.DISABLED)
        self.last_log_state = ""
        self.log_to_terminal(f"[SYSTEM] Initialized Sequence '{self.target_letter}'. Awaiting topological data...", "info")
        
        # ---> SECURE DATABASE UPDATE LOGIC <---
        if self.current_user_id:
            try:
                conn = sqlite3.connect('signlink.db')
                c = conn.cursor()
                c.execute("UPDATE progress SET current_index=? WHERE user_id=?", (self.current_index, self.current_user_id))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[SYSTEM ERROR] Failed to push update to DB: {e}")

    def prev_module(self):
        self.current_index = (self.current_index - 1) % self.total_modules
        self.update_curriculum_ui()

    def next_module(self):
        self.current_index = (self.current_index + 1) % self.total_modules
        self.update_curriculum_ui()

    def video_loop(self):
        ok, frame = self.vs.read()
        if ok:
            frame = cv2.flip(frame, 1)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            black_canvas = np.zeros(frame.shape, dtype=np.uint8) 
            
            results = self.hands.process(cv2image)
            
            if results.multi_hand_landmarks and results.multi_handedness and not self.is_transitioning:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    self.mp_drawing.draw_landmarks(black_canvas, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    hand_type = handedness.classification[0].label 
                    coords = []
                    for lm in hand_landmarks.landmark:
                        x_val = lm.x
                        if hand_type == "Right":  
                            x_val = 1.0 - x_val  
                        coords.extend([x_val, lm.y, lm.z])
                    self.evaluate_topology(coords)
            elif not self.is_transitioning:
                self.hold_frames = max(0, self.hold_frames - 1) 
                self.hold_progress['value'] = (self.hold_frames / self.required_frames) * 100
                self.log_to_terminal("[WARNING] Target lost. No hand structure detected.", "error")

            w1, h1 = self.panel.winfo_width(), self.panel.winfo_height()
            w1, h1 = max(w1, 300), max(h1, 300)
            w2, h2 = self.panel2.winfo_width(), self.panel2.winfo_height()
            w2, h2 = max(w2, 300), max(h2, 300)

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
                
        self.root.after(10, self.video_loop)

    def evaluate_topology(self, coords):
        reshaped_coords = np.array([coords])
        predictions = self.loaded_model.predict(reshaped_coords, verbose=0)
        max_index = np.argmax(predictions[0])
        
        if predictions[0][max_index] > 0.65:
            current_sign = str(self.classes[max_index]) if max_index < len(self.classes) else "--"
            if current_sign == self.target_letter:
                self.hold_frames += 1
                progress_pct = (self.hold_frames / self.required_frames) * 100
                self.hold_progress['value'] = progress_pct
                
                if self.hold_frames == 1:
                    self.log_to_terminal(f"[VALIDATING] Target lock acquired. Hold position...", "warn")
                
                if self.hold_frames >= self.required_frames and not self.is_transitioning:
                    self.is_transitioning = True 
                    self.log_to_terminal(f"[SUCCESS] Matrix '{self.target_letter}' validated! Advancing pipeline...", "success")
                    self.root.after(1000, self.next_module) 
            else:
                if self.hold_frames > 0:
                    self.log_to_terminal(f"[ERROR] Posture deviation. AI tracking '{current_sign}'. Adjust hand.", "error")
                self.hold_frames = max(0, self.hold_frames - 2) 
                self.hold_progress['value'] = (self.hold_frames / self.required_frames) * 100
        else:
            self.hold_frames = max(0, self.hold_frames - 1)
            self.hold_progress['value'] = (self.hold_frames / self.required_frames) * 100

    def destructor(self):
        print("Terminating Diagnostic Engine...")
        self.root.destroy()
        self.vs.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = LearnModule()
    print("[GUI_READY]", flush=True) 
    app.root.mainloop()