import tkinter as tk
from tkinter import ttk, messagebox
import threading
import cv2
from datetime import datetime

class MainWindow:

    def __init__(self, db_session, user_id):
        self.db = db_session
        self.user_id = user_id
        
        self.root = tk.Tk()
        self.root.title("EyeGuard Pro - Защита зрения")
        self.root.geometry("800x600")
        
        self.screen_tracker = None
        self.eye_tracker = None
        self.is_tracking = False
        
        self._create_widgets()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _create_widgets(self):
        title_label = tk.Label(
            self.root,
            text="EyeGuard Pro",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=10)
        
        stats_frame = tk.Frame(self.root)
        stats_frame.pack(pady=10, padx=20, fill="x")
        
        self.time_label = tk.Label(
            stats_frame,
            text="Время работы: 0 мин",
            font=("Arial", 12)
        )
        self.time_label.pack(side="left", padx=10)
        
        self.fatigue_label = tk.Label(
            stats_frame,
            text="Усталость: -",
            font=("Arial", 12)
        )
        self.fatigue_label.pack(side="left", padx=10)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.start_btn = tk.Button(
            btn_frame,
            text="Начать отслеживание",
            command=self.start_tracking,
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="Остановить",
            command=self.stop_tracking,
            bg="#f44336",
            fg="white",
            padx=20,
            pady=10,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        self.break_btn = tk.Button(
            btn_frame,
            text="Взять перерыв",
            command=self.take_break,
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=10
        )
        self.break_btn.pack(side="left", padx=5)
        
        table_frame = tk.Frame(self.root)
        table_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        columns = ('ID', 'Start Time', 'Duration', 'Breaks')
        self.sessions_tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        for col in columns:
            self.sessions_tree.heading(col, text=col)
            self.sessions_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", 
                                  command=self.sessions_tree.yview)
        self.sessions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sessions_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.load_sessions()
        
        self._update_stats()
    
    def start_tracking(self):
        from tracker import ScreenTracker, EyeTracker
        
        self.is_tracking = True

        self.screen_tracker = ScreenTracker(self.user_id, self.db)
        self.screen_tracker.start_session()
        self.screen_tracker.start()
        
        self.eye_tracker = EyeTracker(db_session=self.db)
        self.eye_tracker.start()
        
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        messagebox.showinfo("EyeGuard", "Отслеживание начато!")
    
    def stop_tracking(self):
        self.is_tracking = False
        
        if self.screen_tracker:
            self.screen_tracker.end_session()
            self.screen_tracker.stop()
        
        if self.eye_tracker:
            self.eye_tracker.stop()
        
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

        self.load_sessions()
        
        messagebox.showinfo("EyeGuard", "Отслеживание остановлено")
    
    def take_break(self):
        if self.screen_tracker:
            self.screen_tracker.add_break()
            messagebox.showinfo("Перерыв", "Время для перерыва! Отдохните 5 минут.")
    
    def load_sessions(self):
        from database import Session
        
        for item in self.sessions_tree.get_children():
            self.sessions_tree.delete(item)

        sessions = Session.query.filter_by(user_id=self.user_id).all()
        for session in sessions:
            duration = session.total_minutes if session.total_minutes else "Active"
            self.sessions_tree.insert('', 'end', values=(
                session.id,
                session.start_time.strftime('%Y-%m-%d %H:%M'),
                f"{duration} мин",
                session.break_count
            ))
    
    def _update_stats(self):
        if self.is_tracking and self.screen_tracker:
            if self.screen_tracker.start_time:
                delta = datetime.now() - self.screen_tracker.start_time
                minutes = int(delta.total_seconds() / 60)
                self.time_label.config(text=f"Время работы: {minutes} мин")

        if self.eye_tracker:
            if self.eye_tracker.fatigue_detected:
                self.fatigue_label.config(text="Усталость: ВЫСОКАЯ", fg="red")
            else:
                self.fatigue_label.config(text="Усталость: Нормальная", fg="green")

        self.root.after(1000, self._update_stats)
    
    def on_closing(self):
        if messagebox.askokcancel("Выход", "Завершить приложение?"):
            if self.is_tracking:
                self.stop_tracking()
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()
