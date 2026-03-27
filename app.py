import os
import shutil
import re
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-dev-key')  # Needed for flash messages

def sanitize_name(name):
    sanitized = re.sub(r'[^\w\-]', '_', name)
    return sanitized.strip('_')

def get_all_origamis():
    try:
        types = [d for d in os.listdir("data") if os.path.isdir(os.path.join("data", d))]
        return types
    except FileNotFoundError:
        return []

@app.route('/')
def index():
    origamis = get_all_origamis()
    return render_template('index.html', origamis=origamis)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        name = sanitize_name(name)

        if not name:
            flash('Invalid origami name.', 'danger')
            return redirect(url_for('create'))

        if name in get_all_origamis():
            flash(f'Origami "{name}" already exists.', 'warning')
            return redirect(url_for('index'))

        try:
            os.makedirs(f"data/{name}/images/train", exist_ok=True)
            os.makedirs(f"data/{name}/images/val", exist_ok=True)
            os.makedirs(f"data/{name}/labels/train", exist_ok=True)
            os.makedirs(f"data/{name}/labels/val", exist_ok=True)
            os.makedirs(f"videos", exist_ok=True)
            os.makedirs(f"models/yolo", exist_ok=True)

            flash(f'Origami "{name}" created successfully.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error creating origami: {e}', 'danger')
            return redirect(url_for('create'))

    return render_template('create.html')

@app.route('/edit/<name>', methods=['GET', 'POST'])
def edit(name):
    if name not in get_all_origamis():
        flash(f'Origami "{name}" not found.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_name = request.form.get('new_name', '').strip()
        new_name = sanitize_name(new_name)

        if not new_name:
            flash('Invalid new name.', 'danger')
            return redirect(url_for('edit', name=name))

        if new_name == name:
            flash('Name is the same as the old one.', 'warning')
            return redirect(url_for('index'))

        if new_name in get_all_origamis():
            flash(f'Origami "{new_name}" already exists.', 'warning')
            return redirect(url_for('edit', name=name))

        try:
            # Rename data directory
            if os.path.exists(f"data/{name}"):
                os.rename(f"data/{name}", f"data/{new_name}")

            # Rename video
            if os.path.exists(f"videos/{name}.avi"):
                os.rename(f"videos/{name}.avi", f"videos/{new_name}.avi")

            # Rename model directory
            if os.path.exists(f"models/yolo/{name}"):
                os.rename(f"models/yolo/{name}", f"models/yolo/{new_name}")

            flash(f'Origami "{name}" renamed to "{new_name}".', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error renaming origami: {e}', 'danger')
            return redirect(url_for('edit', name=name))

    return render_template('edit.html', name=name)

@app.route('/delete/<name>', methods=['POST'])
def delete(name):
    if name not in get_all_origamis():
        flash(f'Origami "{name}" not found.', 'danger')
        return redirect(url_for('index'))

    try:
        if os.path.exists(f"data/{name}"):
            shutil.rmtree(f"data/{name}")

        if os.path.exists(f"videos/{name}.avi"):
            os.remove(f"videos/{name}.avi")

        if os.path.exists(f"models/yolo/{name}"):
            shutil.rmtree(f"models/yolo/{name}")

        flash(f'Origami "{name}" deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting origami: {e}', 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
