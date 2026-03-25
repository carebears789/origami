import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import os
import re
import threading

class AdminApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Origami Tutor - Admin Panel")
        self.master.geometry("600x400")

        self.setup_ui()

    def setup_ui(self):
        # Title
        tk.Label(self.master, text="Admin Panel: Manage Origami", font=("Helvetica", 16)).pack(pady=10)

        # Origami Type Input
        frame_input = tk.Frame(self.master)
        frame_input.pack(pady=10)
        tk.Label(frame_input, text="Origami Name:").pack(side=tk.LEFT, padx=5)
        self.origami_name_var = tk.StringVar()
        self.entry_name = tk.Entry(frame_input, textvariable=self.origami_name_var)
        self.entry_name.pack(side=tk.LEFT, padx=5)

        # Buttons
        tk.Button(self.master, text="1. Add New Origami", width=25, command=self.add_origami).pack(pady=5)
        tk.Button(self.master, text="2. Record Tutorial Video", width=25, command=self.record_video).pack(pady=5)
        tk.Button(self.master, text="3. Capture Training Images", width=25, command=self.capture_training_images).pack(pady=5)
        tk.Button(self.master, text="4. Train YOLO Model", width=25, command=self.train_yolo).pack(pady=5)

    def sanitize_name(self, name):
        # Keep only alphanumeric characters and underscores/hyphens
        sanitized = re.sub(r'[^\w\-]', '_', name)
        return sanitized.strip('_')

    def add_origami(self):
        name = self.origami_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter an origami name.")
            return

        name = self.sanitize_name(name)
        if not name:
            messagebox.showerror("Error", "Invalid origami name. Please use letters and numbers.")
            return

        self.origami_name_var.set(name)  # Update UI to reflect sanitized name

        # Create directories
        os.makedirs(f"data/{name}/images/train", exist_ok=True)
        os.makedirs(f"data/{name}/images/val", exist_ok=True)
        os.makedirs(f"data/{name}/labels/train", exist_ok=True)
        os.makedirs(f"data/{name}/labels/val", exist_ok=True)
        os.makedirs(f"videos", exist_ok=True)
        # Note: Do NOT pre-create models/{name} otherwise YOLO will increment to {name}2, {name}3, etc.
        os.makedirs(f"models/yolo", exist_ok=True)

        messagebox.showinfo("Success", f"Directories created for '{name}'.")

    def record_video(self):
        name = self.origami_name_var.get().strip()
        name = self.sanitize_name(name)
        if not name:
            messagebox.showerror("Error", "Please enter a valid origami name first.")
            return

        # Start recording video using cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open camera.")
            return

        # Read a frame to get the camera's resolution
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to grab frame from camera.")
            cap.release()
            return

        height, width = frame.shape[:2]

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video_path = f"videos/{name}.avi"
        out = cv2.VideoWriter(video_path, fourcc, 20.0, (width, height))

        messagebox.showinfo("Recording", "Press 'q' in the video window to stop recording.")

        # Write the first frame we already read
        out.write(frame)
        cv2.imshow('Recording Tutorial', frame)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            out.write(frame)
            cv2.imshow('Recording Tutorial', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        out.release()
        cv2.destroyAllWindows()

        messagebox.showinfo("Success", f"Video saved to {video_path}")

    def capture_training_images(self):
        name = self.origami_name_var.get().strip()
        name = self.sanitize_name(name)
        if not name:
            messagebox.showerror("Error", "Please enter a valid origami name first.")
            return

        # Start capturing images
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open camera.")
            return

        img_save_dir = f"data/{name}/images/train"
        label_save_dir = f"data/{name}/labels/train"
        os.makedirs(img_save_dir, exist_ok=True)
        os.makedirs(label_save_dir, exist_ok=True)

        count = 0
        messagebox.showinfo("Capture", "Press 's' to save an image and draw bounding box. Press 'q' to quit.")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow('Capture Training Data', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                # Pause stream and let user select ROI
                roi = cv2.selectROI('Capture Training Data', frame, fromCenter=False, showCrosshair=True)
                # roi = (x, y, w, h)
                x, y, w, h = roi

                if w > 0 and h > 0:
                    img_path = os.path.join(img_save_dir, f"{name}_{count}.jpg")
                    cv2.imwrite(img_path, frame)

                    # Convert to YOLO format (x_center, y_center, width, height) normalized to 0-1
                    height_img, width_img = frame.shape[:2]
                    x_center = (x + w / 2) / width_img
                    y_center = (y + h / 2) / height_img
                    w_norm = w / width_img
                    h_norm = h / height_img

                    label_path = os.path.join(label_save_dir, f"{name}_{count}.txt")
                    with open(label_path, "w") as f:
                        # Class ID is 0 since nc: 1
                        f.write(f"0 {x_center} {y_center} {w_norm} {h_norm}\n")

                    print(f"Saved {img_path} and label.")
                    count += 1

                # Close the ROI selector window if selectROI created one internally, but typically we just waitKey
            elif key == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        messagebox.showinfo("Success", f"Captured {count} images with labels to {img_save_dir}")

    def train_yolo(self):
        name = self.origami_name_var.get().strip()
        name = self.sanitize_name(name)
        if not name:
            messagebox.showerror("Error", "Please enter a valid origami name first.")
            return

        yaml_content = f"""
train: {os.path.abspath(f'data/{name}/images/train')}
val: {os.path.abspath(f'data/{name}/images/train')}
nc: 1
names: ['{name}']
"""
        yaml_path = f"data/{name}/data.yaml"
        with open(yaml_path, "w") as f:
            f.write(yaml_content)

        # Start a thread so the UI doesn't freeze
        threading.Thread(target=self._run_yolo_train_thread, args=(yaml_path, name), daemon=True).start()

    def _run_yolo_train_thread(self, yaml_path, name):
        try:
            # We assume ultralytics is installed. Import here to avoid loading on startup
            from ultralytics import YOLO
            self.master.after(0, messagebox.showinfo, "Training", "YOLO training has started. Check console for progress.")
            model = YOLO('yolov8n.pt')
            # Set to 1 epoch for prototype
            model.train(data=yaml_path, epochs=1, project='models/yolo', name=name, exist_ok=True)
            self.master.after(0, messagebox.showinfo, "Success", f"YOLO model trained and saved to models/yolo/{name}")
        except Exception as e:
            self.master.after(0, messagebox.showerror, "Error", f"Failed to train model: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdminApp(root)
    root.mainloop()