import cv2
import os
import threading
import time

def record_video(name):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return False

    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to grab frame from camera.")
        cap.release()
        return False

    height, width = frame.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_path = f"videos/{name}.avi"
    out = cv2.VideoWriter(video_path, fourcc, 20.0, (width, height))

    print("Recording: Press 'q' in the video window to stop recording.")
    out.write(frame)
    cv2.imshow(f'Recording Tutorial: {name}', frame)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        out.write(frame)
        cv2.imshow(f'Recording Tutorial: {name}', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Success: Video saved to {video_path}")
    return True

def capture_training_images(name):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return False

    img_save_dir = f"data/{name}/images/train"
    label_save_dir = f"data/{name}/labels/train"
    os.makedirs(img_save_dir, exist_ok=True)
    os.makedirs(label_save_dir, exist_ok=True)

    count = 0
    print("Capture: Press 's' to save an image and draw bounding box. Press 'q' to quit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow(f'Capture Training Data: {name}', frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            roi = cv2.selectROI(f'Capture Training Data: {name}', frame, fromCenter=False, showCrosshair=True)
            x, y, w, h = roi

            if w > 0 and h > 0:
                img_path = os.path.join(img_save_dir, f"{name}_{count}.jpg")
                cv2.imwrite(img_path, frame)

                height_img, width_img = frame.shape[:2]
                x_center = (x + w / 2) / width_img
                y_center = (y + h / 2) / height_img
                w_norm = w / width_img
                h_norm = h / height_img

                label_path = os.path.join(label_save_dir, f"{name}_{count}.txt")
                with open(label_path, "w") as f:
                    f.write(f"0 {x_center} {y_center} {w_norm} {h_norm}\n")

                print(f"Saved {img_path} and label.")
                count += 1
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Success: Captured {count} images with labels to {img_save_dir}")
    return True

def train_yolo(name):
    yaml_content = f"""
train: {os.path.abspath(f'data/{name}/images/train')}
val: {os.path.abspath(f'data/{name}/images/train')}
nc: 1
names: ['{name}']
"""
    yaml_path = f"data/{name}/data.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    def _run_yolo_train_thread(yaml_path, name):
        try:
            from ultralytics import YOLO
            print("Training: YOLO training has started. Check console for progress.")
            model = YOLO('yolov8n.pt')
            model.train(data=yaml_path, epochs=1, project='models/yolo', name=name, exist_ok=True)
            print(f"Success: YOLO model trained and saved to models/yolo/{name}")
        except Exception as e:
            print(f"Error: Failed to train model: {e}")

    threading.Thread(target=_run_yolo_train_thread, args=(yaml_path, name), daemon=True).start()
    return True

def play_tutorial_video(name):
    video_path = f"videos/{name}.avi"
    if not os.path.exists(video_path):
        print(f"Error: Tutorial video for {name} not found.")
        return False

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open tutorial video.")
        return False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow(f"Tutorial: {name}", frame)
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return True

def start_folding_session(name):
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: ultralytics package not installed.")
        return False

    model_path = f"models/yolo/{name}/weights/best.pt"
    if not os.path.exists(model_path):
        print(f"Warning: Custom YOLO model not found at {model_path}. Using base model.")
        model_path = "yolov8n.pt"

    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"Error: Failed to load YOLO model: {e}")
        return False

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return False

    print("Folding Session: Started folding session. Press 'q' in the window to quit. Press 'f' to get feedback from LLM.")

    # We will use this list to store the latest feedback string to draw on the screen
    shared_feedback = ["Press 'f' for feedback"]

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(source=frame, show=False, conf=0.5)
        annotated_frame = results[0].plot()

        # Draw the latest feedback on the frame
        cv2.putText(annotated_frame, shared_feedback[0], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow(f"Folding Session: {name}", annotated_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('f'):
            detected_classes = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    detected_classes.append(model.names[cls_id])
            get_llm_feedback(name, detected_classes, shared_feedback)

    cap.release()
    cv2.destroyAllWindows()
    return True

def get_llm_feedback(origami_name, detected_classes, shared_feedback):
    shared_feedback[0] = "Analyzing folding progress..."

    def _fetch_llm_feedback_thread(origami_name, detected_classes, shared_feedback):
        try:
            import openai
        except ImportError:
            shared_feedback[0] = "Error: openai package not installed."
            return

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            shared_feedback[0] = "No OPENAI_API_KEY found."
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
            shared_feedback[0] = feedback

        except Exception as e:
            shared_feedback[0] = f"Error fetching LLM feedback: {e}"

    threading.Thread(target=_fetch_llm_feedback_thread, args=(origami_name, detected_classes, shared_feedback), daemon=True).start()
