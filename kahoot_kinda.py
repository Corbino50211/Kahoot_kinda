from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import qrcode
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizzes.db'  # For testing locally
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(250), nullable=False)
    options = db.Column(db.String(500), nullable=False)  # Stored as a single string separated by | 
    correct_answer = db.Column(db.String(100), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

# Routes
@app.route('/')
def home():
    quizzes = Quiz.query.all()
    return render_template('quiz_list.html', quizzes=quizzes)

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if request.method == 'POST':
        name = request.form['quiz_name']
        quiz = Quiz(name=name)
        db.session.add(quiz)
        db.session.commit()

        num_questions = int(request.form['num_questions'])
        for i in range(num_questions):
            question_text = request.form.get(f'question_{i}')
            options = request.form.get(f'options_{i}')
            correct_answer = request.form.get(f'correct_answer_{i}')
            question = Question(
                question_text=question_text,
                options=options,
                correct_answer=correct_answer,
                quiz_id=quiz.id
            )
            db.session.add(question)
        db.session.commit()

        # Generate QR code with quiz link
        qr_link = url_for('join_quiz', quiz_id=quiz.id, _external=True)
        qr = qrcode.make(qr_link)
        qr_path = os.path.join('static', f'quiz_qr_{quiz.id}.png')
        qr.save(qr_path)

        return redirect(url_for('home'))

    return render_template('create_quiz.html')

@app.route('/join_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def join_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        player_name = request.form['player_name']
        return redirect(url_for('play_quiz', quiz_id=quiz_id, player=player_name))
    return render_template('join_quiz.html', quiz=quiz)

@app.route('/play_quiz/<int:quiz_id>/<player>', methods=['GET'])
def play_quiz(quiz_id, player):
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('play_quiz.html', quiz=quiz, player=player)

if __name__ == '__main__':
    if not os.path.exists('quizzes.db'):
        with app.app_context():
            db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
