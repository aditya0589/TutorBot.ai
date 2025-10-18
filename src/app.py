from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf import FlaskForm
from langchain.memory import ConversationBufferMemory
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
import bcrypt
from flask_mysqldb import MySQL
import os
from tutor import SubjectTutor
from markdown import markdown as md  # Use markdown for rendering
from dotenv import load_dotenv
import re
import json
import time
import pandas as pd
import plotly.express as px

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

# Define subjects for the notes and progress forms
SUBJECTS = ['dsa', 'ml', 'dbms', 'os', 'webdev', 'networks']

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
    subject = SelectField('Subject', choices=[(s, s.capitalize()) for s in SUBJECTS], validators=[DataRequired()])
    note_content = TextAreaField('Note Content', validators=[DataRequired(), Length(max=10000, message="Note content must not exceed 10,000 characters")])
    submit = SubmitField('Save Note')

class SettingsForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_username = StringField('New Username', validators=[Length(min=2, max=50)])
    new_password = PasswordField('New Password', validators=[Length(min=6, message="Password must be at least 6 characters")])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password', message="Passwords must match")])
    submit = SubmitField('Save Changes')

    def validate_current_password(self, field):
        if 'user_id' in session:
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT password FROM users WHERE id = %s', (session['user_id'],))
            user = cursor.fetchone()
            cursor.close()
            if user and not bcrypt.checkpw(field.data.encode('utf-8'), user[0].encode('utf-8')):
                raise ValidationError('Current password is incorrect.')

# Define topics per subject for quiz context
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

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM quiz_attempts')

    rows = cursor.fetchall()
    col_names = [i[0] for i in cursor.description]
    cursor.close()
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=col_names)

    # Create a column for correctness
    df['marks'] = df['correct_option'] == df['user_option']
    df['marks'] = df['marks'].astype(int)

    accuracy_df = df.groupby('subject').agg(
        total_questions=('marks', 'count'),
        correct_answers=('marks', 'sum')
    ).reset_index()

    accuracy_df['accuracy'] = (accuracy_df['correct_answers'] / accuracy_df['total_questions']) * 100
    accuracy_df['accuracy'] = accuracy_df['accuracy'].round(2)

    # Subject-wise bargraph
    bar_fig = px.bar(
        accuracy_df,
        x='subject',
        y='accuracy',
        color='subject',
        title='Accuracy per Subject (%)',
        labels={'accuracy': 'Accuracy (%)'},
        text='accuracy'
    )

    bar_fig.update_traces(textposition='outside')
    bar_fig.update_layout(
        yaxis_range=[0, 100],
        height=600,
        width=1000,
    )
    sub_bar = bar_fig.to_html(full_html=False)
    

    # Subject-wise line graph for trend analysis
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['date'] = df['created_at'].dt.date

    accuracy_df_2 = df.groupby(['subject', 'date']).agg(
        total_attempts=('marks', 'count'),
        correct_answers=('marks', 'sum')
    ).reset_index()

    accuracy_df_2['accuracy_percent'] = (accuracy_df_2['correct_answers'] / accuracy_df_2['total_attempts']) * 100
    accuracy_df_2['accuracy_percent'] = accuracy_df_2['accuracy_percent'].round(2)

    line_fig = px.line(
        accuracy_df_2,
        x='date',
        y='accuracy_percent',
        color='subject',
        markers = True,
        title='Performance Over Time by Subject',
        labels={
            'date': 'Date',
            'marks percentage': 'Marks(%)',
            'subject': 'Subject'
        }
    )

    line_fig.update_layout(
        yaxis=dict(range=[0, 1]),
        xaxis=dict(
        range=[0, accuracy_df_2['date'].max()]
        ),
        xaxis_title='Date',
        yaxis_title='Marks (%)',
        xaxis_autorange=True,
        yaxis_autorange=True,
        autosize=True,
        height=600,
        width=1000,
        margin=dict(l=40, r=40, t=80, b=40)
    )

    sub_line = line_fig.to_html(full_html=False)

    # Topic-wise bargraph

    accuracy_df_3 = df.groupby(['subject', 'topic']).agg(
        total_questions=('marks', 'count'),
        correct_answers=('marks', 'sum')
    ).reset_index()

    accuracy_df_3['accuracy_percent'] = (accuracy_df_3['correct_answers'] / accuracy_df_3['total_questions']) * 100
    accuracy_df_3['accuracy_percent'] = accuracy_df_3['accuracy_percent'].round(2)

    print(accuracy_df_3.columns)

    bar_dsa = px.bar(
        accuracy_df_3[accuracy_df_3['subject'] == 'dsa'],
        x='topic',
        y='accuracy_percent',
        color='topic',
        title='Accuracy per Topic (%)',
        labels={'accuracy': 'Accuracy (%)'},
        text='accuracy_percent'
    )

    bar_ml = px.bar(
        accuracy_df_3[accuracy_df_3['subject'] == 'ml'],
        x='topic',
        y='accuracy_percent',
        color='topic',
        title='Accuracy per Topic (%)',
        labels={'accuracy': 'Accuracy (%)'},
        text='accuracy_percent'
    )

    bar_dbms = px.bar(
        accuracy_df_3[accuracy_df_3['subject'] == 'dbms'],
        x='topic',
        y='accuracy_percent',
        color='topic',
        title='Accuracy per Topic (%)',
        labels={'accuracy': 'Accuracy (%)'},
        text='accuracy_percent'
    )

    bar_os = px.bar(
        accuracy_df_3[accuracy_df_3['subject'] == 'os'],
        x='topic',
        y='accuracy_percent',
        color='topic',
        title='Accuracy per Topic (%)',
        labels={'accuracy': 'Accuracy (%)'},
        text='accuracy_percent'
    )

    bar_webdev = px.bar(
        accuracy_df_3[accuracy_df_3['subject'] == 'webdev'],
        x='topic',
        y='accuracy_percent',
        color='topic',
        title='Accuracy per Topic (%)',
        labels={'accuracy': 'Accuracy (%)'},
        text='accuracy_percent'
    )

    bar_networks = px.bar(
        accuracy_df_3[accuracy_df_3['subject'] == 'networks'],
        x='topic',
        y='accuracy_percent',
        color='topic',
        title='Accuracy per Topic (%)',
        labels={'accuracy': 'Accuracy (%)'},
        text='accuracy_percent'
    )

    bar_dsa.update_traces(textposition='outside')
    bar_dsa.update_layout(
        yaxis_range=[0, 100],
        height=600,
        width=1000,
    )
    sub_dsa = bar_dsa.to_html(full_html=False)

    bar_ml.update_traces(textposition='outside')
    bar_ml.update_layout(
        yaxis_range=[0, 100],
        height=600,
        width=1000,
    )
    sub_ml = bar_ml.to_html(full_html=False)

    bar_dbms.update_traces(textposition='outside')
    bar_dbms.update_layout(
        yaxis_range=[0, 100],
        height=600,
        width=1000,
    )
    sub_dbms = bar_dbms.to_html(full_html=False)

    bar_os.update_traces(textposition='outside')
    bar_os.update_layout(
        yaxis_range=[0, 100],
        height=600,
        width=1000,
    )
    sub_os = bar_os.to_html(full_html=False)

    bar_webdev.update_traces(textposition='outside')
    bar_webdev.update_layout(
        yaxis_range=[0, 100],
        height=600,
        width=1000,
    )
    sub_webdev = bar_webdev.to_html(full_html=False)

    bar_networks.update_traces(textposition='outside')
    bar_networks.update_layout(
        yaxis_range=[0, 100],
        height=600,
        width=1000,
    )
    sub_networks = bar_networks.to_html(full_html=False)
    return render_template('user_dashboard.html', sub_bar = sub_bar, sub_line = sub_line, sub_dsa = sub_dsa, sub_ml = sub_ml, sub_dbms = sub_dbms, sub_os = sub_os, sub_webdev = sub_webdev, sub_networks = sub_networks)

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
    
    print(data)
    cursor.close()
    return data

# Tracking progress for each subject
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

    # Pre-select the subject in the form
    form.subject.data = subject

    if form.validate_on_submit():
        note_content = form.note_content.data
        user_id = session['user_id']
        
        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                'INSERT INTO user_notes (user_id, subject, note_content) VALUES (%s, %s, %s)',
                (user_id, form.subject.data, note_content)
            )
            mysql.connection.commit()
            # Update progress
            cursor.execute(
                url_for('update_user_progress'),
                {'subject': subject, 'action': 'note'}
            )
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

@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    form = NotesForm()
    notes = []

    if form.validate_on_submit():
        note_content = form.note_content.data
        subject = form.subject.data
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

    # Fetch all notes for the user
    try:
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT id, subject, note_content, created_at FROM user_notes WHERE user_id = %s ORDER BY created_at DESC',
            (session['user_id'],)
        )
        notes = cursor.fetchall()
        cursor.close()
    except Exception as e:
        flash(f'Error fetching notes: {str(e)}', 'error')
        cursor.close()

    return render_template('notes.html', form=form, notes=notes)


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    tutor = SubjectTutor()
    quiz_data = session.get('quiz_data', None)

    if request.method == 'POST':
        subject = request.form.get('subject')
        level = request.form.get('level')
        topic = request.form.get('topic')
        num_questions = int(request.form.get('num_questions', 5))  # Default to 5 if not set

        # Store subject and topic in session for later use
        session['quiz_context'] = {'subject': subject, 'topic': topic}

        # Generate quiz with explanations
        query = f"Generate {num_questions} multiple-choice questions on {subject} for {level} level, focusing on {topic}.Each question should have a question text, 4 options (a, b, c, d), one correct answer, and a brief explanation of the correct answer. Return the response as a JSON object with a 'questions' array, where each question is an object with 'question', 'options' (array of 4), 'correct_answer' (index 0-3), and 'explanation' (string)."
        quiz_raw = tutor.generate_response(subject, query)
        
        # Debug: Print the raw response and its length
        #print(f"Raw quiz response (length: {len(quiz_raw)}): {quiz_raw}")
        
        try:
            # Attempt to extract JSON from code block
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', quiz_raw, re.DOTALL)
            if json_match:
                quiz_raw = json_match.group(1).strip()
                #print(f"Extracted JSON: {quiz_raw}")
            # Fallback to raw JSON if it starts with {
            elif quiz_raw.strip().startswith('{'):
                quiz_raw = quiz_raw.strip()
                #print(f"Using raw JSON: {quiz_raw}")
            else:
                raise ValueError("No valid JSON structure detected in response")
            
            # Validate and parse JSON
            quiz_data = json.loads(quiz_raw)
            if not isinstance(quiz_data, dict) or 'questions' not in quiz_data:
                raise ValueError("Invalid quiz data structure: Missing 'questions' key or not a dictionary")
            
            # Store quiz data in session
            session['quiz_data'] = quiz_data
            flash(f'Quiz generated for {subject} - {topic} ({level}, {num_questions} questions)', 'success')
        except (json.JSONDecodeError, ValueError) as e:
            flash(f'Error parsing quiz data: {str(e)}. Please try again with different parameters.', 'error')
            quiz_data = None
            print(f"JSON parsing failed. Error: {str(e)}, Raw response: {quiz_raw}")  # Detailed debug

    return render_template('quiz.html', quiz_data=quiz_data, topics=TOPICS)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    # Retrieve quiz data and context from session
    quiz_data = session.get('quiz_data')
    quiz_context = session.get('quiz_context', {'subject': '', 'topic': ''})
    print(f"Quiz context during submission: {quiz_context}")  # Debug print
    if not quiz_data:
        flash('No quiz data available. Please generate a quiz first.', 'error')
        return redirect(url_for('quiz'))

    score = 0
    total_questions = len(quiz_data['questions'])
    user_answers = {}  # Store user answers for review
    
    # Debug: Print all received form data
    print(f"Received form data: {dict(request.form)}")
    
    # Compare user answers with correct answers and log to database
    cursor = mysql.connection.cursor()
    for i in range(total_questions):
        user_answer = request.form.get(f'answer_{i}')
        correct_answer_index = quiz_data['questions'][i]['correct_answer']
        print(f"Question {i}: User answer = {user_answer}, Correct answer index = {correct_answer_index}")
        if user_answer is not None:
            # Clean user input to handle letter input (e.g., "a", "b")
            user_answer_cleaned = user_answer.strip().lower()
            if user_answer_cleaned in ['a', 'b', 'c', 'd']:
                user_index = ord(user_answer_cleaned) - ord('a')
                if user_index == correct_answer_index:
                    score += 1
            user_answers[i] = user_answer
            
            # Insert into quiz_attempts table with subject and topic
            cursor.execute(
                """
                INSERT INTO quiz_attempts (user_id, quiz_no, question, option1, option2, option3, option4, correct_option, user_option, subject, topic)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session['user_id'],
                    int(round(time.time())),  # Using timestamp as a proxy for quiz_no
                    quiz_data['questions'][i]['question'],
                    quiz_data['questions'][i]['options'][0],
                    quiz_data['questions'][i]['options'][1],
                    quiz_data['questions'][i]['options'][2],
                    quiz_data['questions'][i]['options'][3],
                    correct_answer_index+1,
                    user_index+1,
                    quiz_context.get('subject', ''),
                    quiz_context.get('topic', ''),
                )
            )
    
    mysql.connection.commit()
    # Update progress with the quiz score (percentage)
    percentage = (score / total_questions) * 100 if total_questions > 0 else 0
    cursor.execute(
        'INSERT IGNORE INTO user_progress (user_id, topic_id) VALUES (%s, %s)',
        (session['user_id'], quiz_context.get('topic'))
    )
    cursor.close()
    
    # Store user answers and score in session for review
    session['quiz_results'] = {
        'score': score,
        'total_questions': total_questions,
        'percentage': percentage,
        'user_answers': user_answers,
        'quiz_data': quiz_data
    }
    
    flash(f'Quiz submitted! Your score: {score}/{total_questions} ({percentage:.1f}%)', 'success')
    return redirect(url_for('quiz'))

@app.route('/review_quiz')
def review_quiz():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    quiz_results = session.get('quiz_results')
    if not quiz_results:
        flash('No quiz results available. Please take a quiz first.', 'error')
        return redirect(url_for('quiz'))
    
    score = quiz_results['score']
    total_questions = quiz_results['total_questions']
    percentage = quiz_results['percentage']
    user_answers = quiz_results['user_answers']
    quiz_data = quiz_results['quiz_data']
    
    return render_template('review_quiz.html', score=score, total_questions=total_questions, 
                          percentage=percentage, user_answers=user_answers, quiz_data=quiz_data)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    form = SettingsForm()
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT name FROM users WHERE id = %s', (session['user_id'],))
    current_username = cursor.fetchone()[0]
    cursor.close()

    if form.validate_on_submit():
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT password FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()
        if user and bcrypt.checkpw(form.current_password.data.encode('utf-8'), user[0].encode('utf-8')):
            new_username = form.new_username.data.strip() if form.new_username.data else None
            new_password = form.new_password.data.strip() if form.new_password.data else None
            
            if new_username or new_password:
                update_query = 'UPDATE users SET '
                update_params = []
                if new_username:
                    update_query += 'name = %s'
                    update_params.append(new_username)
                if new_password:
                    if new_username:
                        update_query += ', password = %s'
                    else:
                        update_query += 'password = %s'
                    update_params.append(bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()))
                update_query += ' WHERE id = %s'
                update_params.append(session['user_id'])
                
                cursor.execute(update_query, update_params)
                mysql.connection.commit()
                cursor.close()
                flash('Settings updated successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Please provide a new username, password, or both to update.', 'error')
        else:
            flash('Incorrect current password.', 'error')

    return render_template('settings.html', form=form, current_username=current_username)

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    current_password = request.form.get('current_password')
    print(f"Attempting deletion for user_id: {session['user_id']}, password provided: {current_password}")
    if not current_password:
        flash('Current password is required for deletion.', 'error')
        print("No password provided, redirecting to settings")
        return redirect(url_for('settings'))
    
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT password FROM users WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()
    if user and bcrypt.checkpw(current_password.encode('utf-8'), user[0].encode('utf-8')):
        print("Password verified, proceeding with deletion")
        # Delete associated data
        cursor.execute('DELETE FROM user_notes WHERE user_id = %s', (session['user_id'],))
        cursor.execute('DELETE FROM quiz_attempts WHERE user_id = %s', (session['user_id'],))
        cursor.execute('DELETE FROM user_progress WHERE user_id = %s', (session['user_id'],))
        cursor.execute('DELETE FROM users WHERE id = %s', (session['user_id'],))
        mysql.connection.commit()
        cursor.close()
        session.pop('user_id', None)
        flash('Account deleted successfully. Goodbye!', 'success')
        print("Deletion successful, redirecting to index")
        return redirect(url_for('index'))
    else:
        flash('Incorrect current password for account deletion.', 'error')
        print("Incorrect password, redirecting to settings")
        return redirect(url_for('settings'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('quiz_data', None)
    session.pop('quiz_results', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/subjects')
def subjects():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    subjects_data = get_subjects_with_topics()
    return render_template('subjects.html', subjects=subjects_data)

if __name__ == '__main__':
    app.run(debug=True)
