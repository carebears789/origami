import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import os
import threading

class StudentApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Origami Tutor - Student Panel")
        self.master.geometry("800x600")

        self.setup_ui()

    def setup_ui(self):
        # Title
        tk.Label(self.master, text="Student Panel: Learn Origami", font=("Helvetica", 16)).pack(pady=10)

        # Origami Selection
        frame_select = tk.Frame(self.master)
        frame_select.pack(pady=10)
        tk.Label(frame_select, text="Select Origami:").pack(side=tk.LEFT, padx=5)

        self.origami_var = tk.StringVar()
        self.combo_origami = ttk.Combobox(frame_select, textvariable=self.origami_var)
        self.combo_origami.pack(side=tk.LEFT, padx=5)

        # Load available origami types (scan data folder)
        self.load_origami_types()

        # Buttons
        tk.Button(self.master, text="1. Watch Tutorial Video", width=25, command=self.play_tutorial_video).pack(pady=5)
        tk.Button(self.master, text="2. Start Folding Session (YOLO)", width=25, command=self.start_folding_session).pack(pady=5)

        # Feedback area
        tk.Label(self.master, text="Tutor Feedback:").pack(pady=(20, 5))
        self.feedback_text = tk.Text(self.master, height=10, width=80, state=tk.DISABLED)
        self.feedback_text.pack()

    def load_origami_types(self):
        try:
            types = [d for d in os.listdir("data") if os.path.isdir(os.path.join("data", d))]
            self.combo_origami['values'] = types
            if types:
                self.combo_origami.current(0)
        except Exception:
            self.combo_origami['values'] = []

    def play_tutorial_video(self):
        name = self.origami_var.get()
        if not name:
            messagebox.showerror("Error", "Please select an origami to learn.")
            return

        video_path = f"videos/{name}.avi"
        if not os.path.exists(video_path):
            messagebox.showerror("Error", f"Tutorial video for {name} not found.")
            return

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open tutorial video.")
            return

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow(f"Tutorial: {name}", frame)

            # Press 'q' to stop early
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def start_folding_session(self):
        name = self.origami_var.get()
        if not name:
            messagebox.showerror("Error", "Please select an origami to learn.")
            return

        try:
            from ultralytics import YOLO
        except ImportError:
            messagebox.showerror("Error", "ultralytics package not installed.")
            return

        model_path = f"models/yolo/{name}/weights/best.pt"
        if not os.path.exists(model_path):
            messagebox.showwarning("Warning", f"Custom YOLO model not found at {model_path}. Using base model.")
            model_path = "yolov8n.pt"

        try:
            model = YOLO(model_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load YOLO model: {e}")
            return

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open camera.")
            return

        messagebox.showinfo("Folding Session", "Started folding session. Press 'q' in the window to quit.\n\nPress 'f' to get feedback from LLM.")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = model.predict(source=frame, show=False, conf=0.5)

            # Draw results on frame
            annotated_frame = results[0].plot()
            cv2.imshow("Folding Session", annotated_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('f'):
                # Extract class names detected
                detected_classes = []
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        detected_classes.append(model.names[cls_id])

                # Get feedback from LLM
                self.get_llm_feedback(name, detected_classes)

        cap.release()
        cv2.destroyAllWindows()

    def get_llm_feedback(self, origami_name, detected_classes):
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete(1.0, tk.END)
        self.feedback_text.insert(tk.END, "Analyzing folding progress...\n")
        self.feedback_text.config(state=tk.DISABLED)
        self.master.update()

        # Start a new thread for the LLM request so we don't block the video feed
        threading.Thread(target=self._fetch_llm_feedback_thread, args=(origami_name, detected_classes), daemon=True).start()

    def _fetch_llm_feedback_thread(self, origami_name, detected_classes):
        try:
            import openai
        except ImportError:
            self.master.after(0, self.update_feedback, "Error: openai package not installed.")
            return

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            self.master.after(0, self.update_feedback, "No OPENAI_API_KEY environment variable found. Unable to generate LLM feedback.")
            return

        try:
            client = openai.OpenAI(api_key=api_key)
            detected_str = ", ".join(detected_classes) if detected_classes else "nothing"
            prompt = f"The student is trying to fold an origami '{origami_name}'. The camera currently sees: {detected_str}. Give brief, encouraging feedback and advice on what they might need to do next or if they made a mistake. Keep it under 3 sentences."

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful and encouraging origami tutor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )

            feedback = response.choices[0].message.content
            self.master.after(0, self.update_feedback, feedback)

        except Exception as e:
            self.master.after(0, self.update_feedback, f"Error fetching LLM feedback: {e}")

    def update_feedback(self, text):
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete(1.0, tk.END)
        self.feedback_text.insert(tk.END, text)
        self.feedback_text.config(state=tk.DISABLED)
        self.master.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = StudentApp(root)
    root.mainloop()