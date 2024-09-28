from flask import Flask, render_template, abort, redirect, url_for, request, flash, session, g, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from datetime import datetime
from language import get_languages


app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = 'static/images/gallery'


# Connect to SQLite
def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = connect_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


# Define the allowed file extensions for the image
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check if a file has an allowed extension


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    current_language = session.get('language', 'en')
    languages = get_languages()

    if 'user_id' in session:
        return render_template('home.html', logged_in=True, languages=languages, current_language=current_language)
    return render_template('home.html', logged_in=False, languages=languages, current_language=current_language)


@app.route('/register', methods=['GET', 'POST'])
def register():
    current_language = session.get('language', 'en')
    languages = get_languages()

    # Redirect if user is already logged in
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = generate_password_hash(password)

        try:
            # Insert new user into the database
            g.db.execute('INSERT INTO user (username, email, password) VALUES (?, ?, ?)',
                         (username, email, hashed_password))
            g.db.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists!', 'danger')

    return render_template('register.html', languages=languages, current_language=current_language)


@app.route('/login', methods=['GET', 'POST'])
def login():
    current_language = session.get('language', 'en')
    languages = get_languages()
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = g.db
        cursor = conn.cursor()
        cursor.execute('SELECT id, password FROM user WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']  # Use 'user_id' consistently
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html', languages=languages, current_language=current_language)


@app.route('/logout')
def logout():
    # Remove the user from the session
    session.pop('user_id', None)

    flash('You have been logged out.', 'info')

    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view the dashboard.', 'danger')
        return redirect(url_for('login'))

    # Fetch all diary entries for the logged-in user
    entries = g.db.execute(
        'SELECT id, title, content, date_posted, image_path FROM diary_entry WHERE user_id = ?', (user_id,)).fetchall()

    # Fetch tags for each entry
    entry_tags = {}
    for entry in entries:
        tags = g.db.execute('''
            SELECT tags.name
            FROM tags
            JOIN entry_tags ON tags.id = entry_tags.tag_id
            WHERE entry_tags.entry_id = ?
        ''', (entry['id'],)).fetchall()
        entry_tags[entry['id']] = [tag['name'] for tag in tags]

    current_language = session.get('language', 'en')
    languages = get_languages()

    return render_template('dashboard.html', entries=entries, entry_tags=entry_tags, languages=languages, current_language=current_language)


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = g.db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()

    current_language = session.get('language', 'en')
    languages = get_languages()

    return render_template('profile.html', user=user, languages=languages, current_language=current_language)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = g.db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()

    if request.method == 'POST':
        # Get updated form data
        username = request.form['username']
        email = request.form['email']
        name = request.form['name']
        surname = request.form['surname']
        country = request.form['country']
        city = request.form['city']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        profile_image = request.files['profile_image']
        banner_image = request.files['profile_banner']

        # Handle profile image upload
        if profile_image and profile_image.filename != '':
            filename = secure_filename(profile_image.filename)
            profile_image.save(os.path.join('static/images', filename))
            g.db.execute('UPDATE user SET profile_image = ? WHERE id = ?', (filename, user_id))

        # Handle banner image upload
        if banner_image and banner_image.filename != '':
            filename2 = secure_filename(banner_image.filename)
            banner_image.save(os.path.join('static/images', filename2))
            g.db.execute('UPDATE user SET profile_banner = ? WHERE id = ?', (filename2, user_id))

        # Update username and email
        g.db.execute('UPDATE user SET username = ?, email = ?, name = ?, surname = ?, country = ?, city = ? WHERE id = ?',
                     (username, email, name, surname, country, city, user_id))

        # Handle password change if provided
        if password and password == confirm_password:
            hashed_password = generate_password_hash(password)
            g.db.execute('UPDATE user SET password = ? WHERE id = ?', (hashed_password, user_id))

        # Commit the updates
        g.db.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    current_language = session.get('language', 'en')
    languages = get_languages()

    return render_template('edit_profile.html', user=user, languages=languages, current_language=current_language)


@app.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    if 'user_id' not in session:
        flash('Please log in to add an entry.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        date_posted = request.form.get('date_posted')
        tags = request.form.get('tags')  # Get the tags input
        image = request.files.get('image')

        if not title or not content or not date_posted:
            flash('All fields are required!', 'danger')
            return redirect(url_for('add_entry'))

        try:
            # Convert the date_time string to a Python datetime object
            entry_datetime = datetime.strptime(date_posted, '%Y-%m-%dT%H:%M')

            user_id = session['user_id']
            image_path = None

            # Handle the image upload
            if image and image.filename != '':  # Check if the image was uploaded
                filename = secure_filename(image.filename)
                image.save(os.path.join('static/images', filename))  # Save the image
                image_path = filename  # Set image_path to the filename

            # Insert the new diary entry into the database
            cursor = g.db.execute('INSERT INTO diary_entry (title, content, user_id, date_posted, image_path) VALUES (?, ?, ?, ?, ?)',
                                  (title, content, user_id, entry_datetime, image_path))
            entry_id = cursor.lastrowid

            # Handle tags
            if tags:
                tag_list = [tag.strip().lower()
                            for tag in tags.split(',')]  # Split and clean the tags
                for tag in tag_list:
                    cursor = g.db.execute('SELECT id FROM tags WHERE name = ?', (tag,))
                    tag_data = cursor.fetchone()

                    if tag_data:
                        tag_id = tag_data['id']
                    else:
                        cursor = g.db.execute('INSERT INTO tags (name) VALUES (?)', (tag,))
                        tag_id = cursor.lastrowid

                    g.db.execute(
                        'INSERT INTO entry_tags (entry_id, tag_id) VALUES (?, ?)', (entry_id, tag_id))

            g.db.commit()

            flash('Diary entry added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')
            return redirect(url_for('add_entry'))
    current_language = session.get('language', 'en')
    languages = get_languages()

    return render_template('add_entry.html', languages=languages, current_language=current_language)


@app.route('/entry/<int:entry_id>')
def view_entry(entry_id):
    # Fetch the entry data
    entry = g.db.execute('SELECT id, title, content, date_posted, image_path FROM diary_entry WHERE id = ?',
                         (entry_id,)).fetchone()

    if entry is None:
        abort(404)  # Entry not found

    # Fetch the tags associated with this entry
    tags = g.db.execute('''
        SELECT tags.name
        FROM tags
        JOIN entry_tags ON tags.id = entry_tags.tag_id
        WHERE entry_tags.entry_id = ?
    ''', (entry_id,)).fetchall()

    # Instead of creating a comma-separated string, pass the list of tag names
    tag_list = [tag['name'] for tag in tags]

    current_language = session.get('language', 'en')
    languages = get_languages()
    return render_template('view_entry.html', entry=entry, tags=tag_list, languages=languages, current_language=current_language)


@app.route('/edit_entry/<int:entry_id>', methods=['GET', 'POST'])
def edit_entry(entry_id):
    # Fetch the entry from the database
    entry = g.db.execute(
        'SELECT id, title, content, date_posted, image_path FROM diary_entry WHERE id = ?', (entry_id,)).fetchone()
    if entry is None:
        abort(404)  # Entry not found

    # Fetch existing tags for the entry
    existing_tags = g.db.execute('''
        SELECT tags.name
        FROM tags
        JOIN entry_tags ON tags.id = entry_tags.tag_id
        WHERE entry_tags.entry_id = ?
    ''', (entry_id,)).fetchall()

    # Create a comma-separated list of the existing tags for display in the form
    existing_tag_list = ', '.join([tag['name'] for tag in existing_tags])

    if request.method == 'POST':
        # Retrieve the title, content, and tags from the form
        title = request.form['title']
        content = request.form['content']
        date_posted = request.form['date_posted']
        tags = request.form.get('tags')  # Get the tags input
        image_path = entry['image_path']  # Keep the existing image unless changed

        # Handle image upload if a file was submitted
        if 'entry_image' in request.files:
            file = request.files['entry_image']
            if file and allowed_file(file.filename):
                # Secure the filename and save it in the static/images directory
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename  # Update image path with the new file

        # Update the diary entry in the database
        g.db.execute('UPDATE diary_entry SET title = ?, content = ?, date_posted = ?, image_path = ? WHERE id = ?',
                     (title, content, date_posted, image_path, entry_id))

        # Update the tags
        if tags:
            # Clear existing tags
            g.db.execute('DELETE FROM entry_tags WHERE entry_id = ?', (entry_id,))
            tag_list = [tag.strip().lower() for tag in tags.split(',')]  # Split and clean tags
            for tag in tag_list:
                cursor = g.db.execute('SELECT id FROM tags WHERE name = ?', (tag,))
                tag_data = cursor.fetchone()

                if tag_data:
                    tag_id = tag_data['id']
                else:
                    cursor = g.db.execute('INSERT INTO tags (name) VALUES (?)', (tag,))
                    tag_id = cursor.lastrowid

                g.db.execute('INSERT INTO entry_tags (entry_id, tag_id) VALUES (?, ?)',
                             (entry_id, tag_id))

        g.db.commit()

        # Redirect to the view entry page after successful update
        flash('Entry updated successfully!', 'success')
        return redirect(url_for('view_entry', entry_id=entry_id))

    current_language = session.get('language', 'en')
    languages = get_languages()
    return render_template('edit_entry.html', entry=entry, tags=existing_tag_list, languages=languages, current_language=current_language)


@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    g.db.execute('DELETE FROM diary_entry WHERE id = ?', (entry_id,))
    g.db.commit()
    flash('Entry deleted successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/terms')
def terms():
    current_language = session.get('language', 'en')
    languages = get_languages()
    return render_template('terms.html', languages=languages, current_language=current_language)


@app.route('/privacy')
def privacy():
    current_language = session.get('language', 'en')
    languages = get_languages()
    return render_template('privacy.html', languages=languages, current_language=current_language)


@app.route('/about')
def about():
    current_language = session.get('language', 'en')
    languages = get_languages()
    return render_template('about.html', languages=languages, current_language=current_language)


@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'user_id' not in session:
        flash('Please log in to upload an image.', 'danger')
        return redirect(url_for('login'))

    # Check if the post request has the file part
    if 'image' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('gallery'))

    file = request.files['image']

    # If user does not select a file, browser also
    # submits an empty part without filename
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('gallery'))

    if file and allowed_file(file.filename):
        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        file.save(os.path.join('static/images/gallery', filename))

        # Insert image into the gallery table with user_id
        user_id = session['user_id']
        g.db.execute('INSERT INTO gallery (user_id, image_path) VALUES (?, ?)', (user_id, filename))
        g.db.commit()

        flash('Image uploaded successfully!', 'success')
    else:
        flash('Invalid file type. Only png, jpg, jpeg, gif are allowed.', 'danger')

    return redirect(url_for('gallery'))


@app.route('/gallery')
def gallery():
    if 'user_id' not in session:
        flash('Please log in to view the gallery.', 'danger')
        return redirect(url_for('login'))

    # Fetch images from the gallery table for the logged-in user
    user_id = session['user_id']
    images = g.db.execute(
        'SELECT id, image_path, upload_date FROM gallery WHERE user_id = ?', (user_id,)).fetchall()

    current_language = session.get('language', 'en')
    languages = get_languages()

    return render_template('gallery.html', images=images, languages=languages, current_language=current_language)


@app.route('/image/<int:image_id>')
def view_image(image_id):
    image = g.db.execute('SELECT id, image_path, upload_date FROM gallery WHERE id = ?',
                         (image_id,)).fetchone()

    if image is None:
        abort(404)

    current_language = session.get('language', 'en')
    languages = get_languages()
    return render_template('view_image.html', image=image, languages=languages, current_language=current_language)


@app.route('/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    g.db.execute('DELETE FROM gallery WHERE id = ?', (image_id,))
    g.db.commit()
    flash('Image deleted successfully!', 'success')
    return redirect(url_for('gallery'))


@app.route('/calendar')
def calendar():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view the calendar.', 'danger')
        return redirect(url_for('login'))

    # Fetch all diary entry dates for the logged-in user
    entries = g.db.execute(
        'SELECT date_posted FROM diary_entry WHERE user_id = ?', (user_id,)
    ).fetchall()

    # Convert the results into a list of dates in 'YYYY-MM-DD' format
    entry_dates = [entry['date_posted'].split(' ')[0] for entry in entries]

    current_language = session.get('language', 'en')
    languages = get_languages()

    return render_template('calendar.html', entries=entry_dates, languages=languages, current_language=current_language)


@app.route('/change_language', methods=['POST'])
def change_language():
    data = request.get_json()
    language = data.get('language')

    # Store the selected language in the session
    session['language'] = language
    return jsonify({"message": "Language changed successfully!"}), 200
