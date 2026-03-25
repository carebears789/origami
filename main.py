import tkinter as tk
from tkinter import messagebox
from src.admin import AdminApp
from src.student import StudentApp
import sys
import os

class MainLauncher:
    def __init__(self, master):
        self.master = master
        self.master.title("Origami Tutor - Launcher")
        self.master.geometry("400x300")

        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.master, text="Welcome to Origami Tutor", font=("Helvetica", 18, "bold")).pack(pady=30)

        tk.Button(self.master, text="Enter as Admin (Teacher)", font=("Helvetica", 12), width=25, height=2, command=self.launch_admin).pack(pady=10)
        tk.Button(self.master, text="Enter as Student (Learner)", font=("Helvetica", 12), width=25, height=2, command=self.launch_student).pack(pady=10)

    def launch_admin(self):
        new_window = tk.Toplevel(self.master)
        app = AdminApp(new_window)

    def launch_student(self):
        new_window = tk.Toplevel(self.master)
        app = StudentApp(new_window)

if __name__ == "__main__":
    # Ensure src package can be resolved properly if running from the project root
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    root = tk.Tk()
    app = MainLauncher(root)
    root.mainloop()