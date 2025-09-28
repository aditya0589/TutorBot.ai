from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf import FlaskForm
from langchain.memory import ConversationBufferMemory
from wtforms import SelectField, StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length
import bcrypt
from flask_mysqldb import MySQL
import os
from tutor import SubjectTutor
from markdown import markdown as md  # Use markdown for rendering
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.secret_key = os.urandom(24)

# MySQL connection
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
mysql = MySQL(app)

# Add markdown filter to Jinja2
app.jinja_env.filters['markdown'] = md

class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class NotesForm(FlaskForm):
    subject = SelectField('Subject', choices=[
        ('dsa', 'Data Structures & Algorithms'),
        ('ml', 'Machine Learning'),
        ('dbms', 'Database Systems'),
        ('os', 'Operating Systems'),
        ('webdev', 'Web Development'),
        ('networks', 'Computer Networks')
    ], validators=[DataRequired()])
    note_content = TextAreaField('Note Content', validators=[DataRequired(), Length(max=10000, message="Note content must not exceed 10,000 characters")])
    submit = SubmitField('Save Note')

# Define topics per subject
TOPICS = {
    'dsa': ['Arrays', 'Linked Lists', 'Stacks', 'Queues', 'Trees', 'Graphs', 'Sorting', 'Searching'],
    'ml': ['Supervised Learning', 'Unsupervised Learning', 'Neural Networks', 'Regression', 'Classification'],
    'dbms': ['ER Model', 'Normalization', 'Transactions', 'Indexing', 'SQL'],
    'os': ['Processes', 'Threads', 'Memory Management', 'Scheduling', 'File Systems'],
    'webdev': ['HTML', 'CSS', 'JavaScript', 'React', 'Node.js'],
    'networks': ['OSI Model', 'TCP/IP', 'Routing', 'Subnetting', 'HTTP']
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)', (name, email, hashed_password))
        mysql.connection.commit()
        cursor.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT name FROM users WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    
    if user:
        user_name = user[0]
    else:
        user_name = "Student"
    
    return render_template('home.html', user_name=user_name)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/session')
def session_page():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    return render_template('session.html')

def get_subjects_with_topics():
    cursor = mysql.connection.cursor()

    # Example structure: subjects table & topics table
    cursor.execute("SELECT sub_id, sub_name FROM subjects")
    subjects = cursor.fetchall()

    data = []
    for subj in subjects:
        cursor.execute("SELECT topic_id, topic_name FROM topics WHERE sub_id=%s", (subj[0],))
        topics = cursor.fetchall()
        data.append({"sub_id": subj[0], "sub_name": subj[1], "topics": topics})
    cursor.close()
    return data

#tracking progress for each subject
@app.route('/progress_tracker')
def progress_tracker():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    subjects_data = get_subjects_with_topics()
    # Fetch completed topic ids for the logged-in user
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT topic_id FROM user_progress WHERE user_id = %s', (session['user_id'],))
    completed_rows = cursor.fetchall()
    cursor.close()
    completed_topic_ids = set(row[0] for row in completed_rows)
    # Compute per-subject progress
    for subject in subjects_data:
        total_topics = len(subject["topics"]) if subject.get("topics") else 0
        completed_topics = 0
        if total_topics > 0:
            for topic in subject["topics"]:
                if topic[0] in completed_topic_ids:
                    completed_topics += 1
            progress_pct = int(round((completed_topics / total_topics) * 100))
        else:
            progress_pct = 0
        subject["total_topics"] = total_topics
        subject["completed_topics"] = completed_topics
        subject["progress_pct"] = progress_pct

    return render_template("progress_tracker.html", subjects=subjects_data, completed_topic_ids=completed_topic_ids)


# API endpoint to update user progress per topic
@app.route('/api/progress', methods=['POST'])
def update_user_progress():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        payload = request.get_json(silent=True) or {}
        topic_id = payload.get('topic_id')
        completed = bool(payload.get('completed'))

        if topic_id is None:
            return jsonify({"success": False, "error": "topic_id is required"}), 400

        cursor = mysql.connection.cursor()

        if completed:
            cursor.execute('INSERT IGNORE INTO user_progress (user_id, topic_id) VALUES (%s, %s)', (session['user_id'], topic_id))
        else:
            cursor.execute('DELETE FROM user_progress WHERE user_id = %s AND topic_id = %s', (session['user_id'], topic_id))

        mysql.connection.commit()
        cursor.close()

        return jsonify({"success": True})
    except Exception as e:
        try:
            cursor.close()
        except Exception:
            pass
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/tutors/<subject>_tutor', methods=['GET', 'POST'])
def tutor_page(subject):
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    form = NotesForm()
    existing_note = None
    tutor_response = None
    tutor = SubjectTutor()

    if form.validate_on_submit():
        note_content = form.note_content.data
        user_id = session['user_id']
        
        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                'INSERT INTO user_notes (user_id, subject, note_content) VALUES (%s, %s, %s)',
                (user_id, subject, note_content)
            )
            mysql.connection.commit()
            cursor.close()
            flash('Note saved successfully!', 'success')
        except Exception as e:
            flash(f'Error saving note: {str(e)}', 'error')
            cursor.close()
    
    elif request.method == 'POST' and 'query' in request.form:
        query = request.form['query']
        tutor_response = tutor.generate_response(subject, query)
        # Debug print to check response
        print(f"Tutor response: {tutor_response}")

    else:
        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                'SELECT note_content FROM user_notes WHERE user_id = %s AND subject = %s ORDER BY created_at DESC LIMIT 1',
                (session['user_id'], subject)
            )
            existing_note = cursor.fetchone()
            cursor.close()
        except Exception as e:
            flash(f'Error fetching note: {str(e)}', 'error')
            cursor.close()

    subject_templates = {
        'dsa': 'tutors/dsa_tutor.html',
        'ml': 'tutors/ml_tutor.html',
        'dbms': 'tutors/dbms_tutor.html',
        'os': 'tutors/os_tutor.html',
        'webdev': 'tutors/webdev_tutor.html',
        'networks': 'tutors/networks_tutor.html'
    }
    
    template_name = subject_templates.get(subject)
    if template_name:
        return render_template(template_name, form=form, existing_note=existing_note[0] if existing_note else "", 
                              tutor_response=tutor_response)
    else:
        flash('Subject not found.', 'error')
        return redirect(url_for('session_page'))

@app.route('/review_notes')
def review_notes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor()
    query = "SELECT id, subject, note_content, created_at FROM user_notes WHERE user_id = %s"
    params = [session['user_id']]
    subject = request.args.get('subject', '')
    date_str = request.args.get('date', '')

    if subject:
        query += " AND subject = %s"
        params.append(subject)
    if date_str:
        query += " AND DATE(created_at) = %s"
        params.append(date_str)

    print(f"Query: {query}, Params: {params}")
    cursor.execute(query, params)
    notes = cursor.fetchall()
    cursor.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'notes': [{'id': note[0], 'subject': note[1], 'note_content': note[2], 'created_at': note[3].isoformat()} for note in notes]})

    return render_template('review_notes.html', notes=notes, user_name=session.get('user_name'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    tutor = SubjectTutor()
    quiz_data = None

    if request.method == 'POST':
        subject = request.form.get('subject')
        level = request.form.get('level')
        topic = request.form.get('topic')
        num_questions = int(request.form.get('num_questions', 5))  # Default to 5 if not set

        # Generate quiz using the tutor
        query = f"Generate {num_questions} multiple-choice questions on {subject} for {level} level, focusing on {topic}. Each question should have a question text, 4 options (a, b, c, d), and one correct answer. Return the response as a JSON object with a 'questions' array, where each question is an object with 'question', 'options' (array of 4), and 'correct_answer' (index 0-3)."
        quiz_raw = tutor.generate_response(subject, query)
        
        try:
            import json
            quiz_data = json.loads(quiz_raw)
            flash(f'Quiz generated for {subject} - {topic} ({level}, {num_questions} questions)', 'success')
        except json.JSONDecodeError:
            flash('Error parsing quiz data. Please try again.', 'error')
            quiz_data = None

    return render_template('quiz.html', quiz_data=quiz_data, topics=TOPICS)

@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    form = NotesForm()
    existing_note = None

    if form.validate_on_submit():
        subject = form.subject.data
        note_content = form.note_content.data
        user_id = session['user_id']
        
        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                'INSERT INTO user_notes (user_id, subject, note_content) VALUES (%s, %s, %s)',
                (user_id, subject, note_content)
            )
            mysql.connection.commit()
            cursor.close()
            flash('Note saved successfully!', 'success')
        except Exception as e:
            flash(f'Error saving note: {str(e)}', 'error')
            cursor.close()
    
    else:
        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                'SELECT subject, note_content FROM user_notes WHERE user_id = %s ORDER BY created_at DESC LIMIT 1',
                (session['user_id'],)
            )
            existing_note = cursor.fetchone()
            cursor.close()
            if existing_note:
                form.subject.data = existing_note[0]
                form.note_content.data = existing_note[1]
        except Exception as e:
            flash(f'Error fetching note: {str(e)}', 'error')
            cursor.close()

    return render_template('notes.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
