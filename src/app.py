from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf import FlaskForm
from langchain.memory import ConversationBufferMemory
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length
import bcrypt
from flask_mysqldb import MySQL
import os
from tutor import SubjectTutor
from markdown import markdown as md  # Use markdown for rendering
import re
import json

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
    note_content = TextAreaField('Note Content', validators=[DataRequired(), Length(max=10000, message="Note content must not exceed 10,000 characters")])
    submit = SubmitField('Save Note')

# ---------------------------
# Helper: normalize AI quiz data
# ---------------------------
def normalize_quiz_data(quiz_data):
    """
    Normalizes quiz_data in-place to ensure:
    - For MCQs with 'options': question['correct_answer'] is an int index 0..(n-1)
    - For open-ended: question['correct_answer'] becomes a lowercased string
    Handles AI outputs with keys 'answer', 'correct', or 'correct_answer' (which may be text, letter, or index).
    """
    for q in quiz_data.get('questions', []):
        # unify key names
        if 'correct_answer' not in q:
            q['correct_answer'] = q.get('answer') or q.get('correct') or None

        options = q.get('options') or []
        ca = q.get('correct_answer')

        if options:
            # MCQ handling → convert to 0-based index where possible
            if ca is None:
                q['correct_answer'] = None
                continue

            if isinstance(ca, int):
                # If 0-based within range, ok; if 1-based convert to 0-based
                if 0 <= ca < len(options):
                    q['correct_answer'] = int(ca)
                elif 1 <= ca <= len(options):
                    q['correct_answer'] = int(ca) - 1
                else:
                    q['correct_answer'] = None
                continue

            if isinstance(ca, str):
                s = ca.strip()
                # letter -> index (a->0)
                if len(s) == 1 and s.lower() in {'a','b','c','d','e','f'}:
                    idx = ord(s.lower()) - ord('a')
                    q['correct_answer'] = idx if 0 <= idx < len(options) else None
                    continue

                # numeric string
                if s.isdigit():
                    idx = int(s)
                    if 1 <= idx <= len(options):
                        q['correct_answer'] = idx - 1
                        continue
                    if 0 <= idx < len(options):
                        q['correct_answer'] = idx
                        continue

                # exact match to option text
                matched_index = None
                for opt_i, opt_text in enumerate(options):
                    if opt_text is not None and s.lower() == str(opt_text).strip().lower():
                        matched_index = opt_i
                        break
                if matched_index is not None:
                    q['correct_answer'] = matched_index
                    continue

                # loose containment match
                matched_index = None
                for opt_i, opt_text in enumerate(options):
                    if opt_text is not None and s.lower() in str(opt_text).strip().lower():
                        matched_index = opt_i
                        break
                if matched_index is not None:
                    q['correct_answer'] = matched_index
                    continue

                q['correct_answer'] = None
                continue

            q['correct_answer'] = None
        else:
            # Open-ended: store normalized string
            q['correct_answer'] = None if ca is None else str(ca).strip().lower()

    return quiz_data

# ---------------------------
# Get next quiz number for a user
# ---------------------------
def get_next_quiz_no(user_id):
    """
    Per-user quiz numbering: find max quiz_no for this user and add 1.
    """
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT MAX(quiz_no) FROM quiz_attempts WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        max_q = row[0] if row and row[0] is not None else 0
        return int(max_q) + 1
    except Exception as e:
        print("Error getting next quiz_no:", e)
        return 1

# ---------------------------
# Routes (kept same as original, with small integrations)
# ---------------------------
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

# ---------------------------
# Quiz generation & normalization
# ---------------------------
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

        # Generate quiz with explanations
        query = f"Generate {num_questions} multiple-choice questions on {subject} for {level} level, focusing on {topic}. Each question should have a question text, 4 options (a, b, c, d), one correct answer, and a brief explanation of the correct answer. Return the response as a JSON object with a 'questions' array, where each question is an object with 'question', 'options' (array of 4), 'correct_answer' (index 0-3), and 'explanation' (string)."
        quiz_raw = tutor.generate_response(subject, query)
        
        # Debug: Print the raw response to inspect it
        print(f"Raw quiz response: {quiz_raw}")
        
        try:
            # Extract JSON from the response if it's within a code block
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', quiz_raw, re.DOTALL)
            if json_match:
                quiz_raw = json_match.group(1).strip()
            elif quiz_raw.strip().startswith('{'):
                # If no code block, assume the response starts with JSON
                quiz_raw = quiz_raw.strip()
            else:
                raise ValueError("No valid JSON found in response")
            
            # Validate and parse JSON
            quiz_data = json.loads(quiz_raw)
            if not isinstance(quiz_data, dict) or 'questions' not in quiz_data:
                raise ValueError("Invalid quiz data structure")
            
            # Normalize the AI-provided quiz data (ensures consistent correct_answer format)
            quiz_data = normalize_quiz_data(quiz_data)
            
            # Get and set quiz_no for this generated quiz (per-user)
            quiz_no = get_next_quiz_no(session['user_id'])
            session['quiz_no'] = quiz_no

            # Store quiz data in session
            session['quiz_data'] = quiz_data
            flash(f'Quiz generated for {subject} - {topic} ({level}, {num_questions} questions)', 'success')
        except (json.JSONDecodeError, ValueError) as e:
            flash(f'Error parsing quiz data: {str(e)}. Raw response: {quiz_raw}', 'error')
            quiz_data = None

    return render_template('quiz.html', quiz_data=quiz_data)

# ---------------------------
# Submit quiz (with DB logging) — updated to include user_id and per-user quiz_no
# ---------------------------
@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    # Retrieve quiz data from session
    quiz_data = session.get('quiz_data')
    quiz_no = session.get('quiz_no')  # set when quiz was generated
    user_id = session.get('user_id')
    if not quiz_data:
        flash('No quiz data available. Please generate a quiz first.', 'error')
        return redirect(url_for('quiz'))

    score = 0
    total_questions = len(quiz_data['questions'])
    user_answers = {}  # Store user answers for review
    
    # Debug: Print all received form data
    print(f"Received form data: {dict(request.form)}")
    
    # MySQL cursor
    cursor = mysql.connection.cursor()

    # Compare user answers with correct answers and log each question
    for i in range(total_questions):
        question = quiz_data['questions'][i]
        options = question.get('options') or []
        correct_index = question.get('correct_answer')  # normalized to 0-based index or str (open-ended)
        
        user_answer = request.form.get(f'answer_{i}')
        if user_answer is None:
            # no answer submitted
            continue
        
        ua = user_answer.strip()
        # If MCQ
        if options:
            matched = False
            # 1) If user enters a digit (1-based index), map to 0-based and compare
            if ua.isdigit():
                try:
                    chosen_idx = int(ua) - 1
                    if correct_index is not None and 0 <= chosen_idx < len(options):
                        if int(correct_index) == chosen_idx:
                            score += 1
                            matched = True
                except ValueError:
                    pass

            # 2) If user typed option text, compare case-insensitively with the correct option text
            if not matched:
                try:
                    # compare to correct option text (if correct_index available)
                    if correct_index is not None and 0 <= int(correct_index) < len(options):
                        correct_text = str(options[int(correct_index)]).strip().lower()
                        if ua.lower() == correct_text:
                            score += 1
                            matched = True
                except (ValueError, TypeError, IndexError):
                    pass

            # store raw user answer for review
            user_answers[i] = user_answer
        else:
            # open-ended
            ua_norm = ua.lower()
            correct_text = question.get('correct_answer')
            if correct_text is not None and ua_norm == str(correct_text).strip().lower():
                score += 1
            user_answers[i] = user_answer

        # debug print per question
        print(f"Q{i} - UA: {user_answer} | options: {options} | correct_index: {correct_index} | score so far: {score}")

        # Store in MySQL (include user_id and quiz_no)
        try:
            cursor.execute("""
                INSERT INTO quiz_attempts
                (user_id, quiz_no, question, option1, option2, option3, option4, correct_option, user_option)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                quiz_no,
                question.get('question'),
                options[0] if len(options) > 0 else None,
                options[1] if len(options) > 1 else None,
                options[2] if len(options) > 2 else None,
                options[3] if len(options) > 3 else None,
                (int(correct_index) + 1) if (correct_index is not None and isinstance(correct_index, int)) else None,
                int(ua) if ua.isdigit() else ua
            ))
            mysql.connection.commit()
        except Exception as e:
            # Log error but continue saving other questions
            print(f"Error inserting quiz_attempt for Q{i}: {e}")
            mysql.connection.rollback()

    # Calculate percentage
    percentage = (score / total_questions) * 100 if total_questions > 0 else 0
    
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

# ---------------------------
# Review quiz route (unchanged)
# ---------------------------
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

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('quiz_data', None)
    session.pop('quiz_results', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
