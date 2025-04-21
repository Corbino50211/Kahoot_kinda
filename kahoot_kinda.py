import os
import json
import qrcode
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

if not os.path.exists('static'):
    os.makedirs('static')

# Load quizzes from a file
def load_quizzes():
    try:
        with open('quizzes.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

quizzes = load_quizzes()
players = {}
current_question_index = {}

# Function to save quizzes
def save_quizzes():
    with open('quizzes.json', 'w') as f:
        json.dump(quizzes, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if request.method == 'POST':
        quiz_name = request.form.get('quiz_name')
        question_text = request.form.get('question_text')
        answers = request.form.get('answers').split(',')
        correct_answer = request.form.get('correct_answer')

        if quiz_name and question_text and answers and correct_answer:
            quiz = {
                "quiz_name": quiz_name,
                "questions": [
                    {
                        "text": question_text,
                        "options": [ans.strip() for ans in answers],
                        "answer": correct_answer.strip()
                    }
                ]
            }

            # Add quiz to the quizzes dictionary
            if quiz_name not in quizzes:
                quizzes[quiz_name] = quiz
            else:
                quizzes[quiz_name]['questions'].append({
                    "text": question_text,
                    "options": [ans.strip() for ans in answers],
                    "answer": correct_answer.strip()
                })

            # Save the quizzes to the file
            save_quizzes()
            return redirect(url_for('quiz_list'))

    return render_template('create_quiz.html')

@app.route('/quiz_list')
def quiz_list():
    return render_template('quiz_list.html', quizzes=quizzes)

@app.route('/join_quiz', methods=['GET', 'POST'])
def join_quiz():
    if request.method == 'POST':
        quiz_name = request.form.get('quiz_name')
        player_name = request.form.get('player_name')

        if quiz_name and player_name:
            if quiz_name not in quizzes:
                return "Quiz not found", 404

            if quiz_name not in players:
                players[quiz_name] = {}

            players[quiz_name][player_name] = 0  # Initialize player's score
            current_question_index[quiz_name] = 0  # Start at first question
            return redirect(url_for('quiz', quiz_name=quiz_name, player_name=player_name))

    return render_template('join_quiz.html', quizzes=quizzes)

@app.route('/quiz')
def quiz():
    quiz_name = request.args.get('quiz_name')
    player_name = request.args.get('player_name')

    if quiz_name not in quizzes:
        return "Quiz not found", 404

    quiz = quizzes[quiz_name]

    # Get the current question
    current_index = current_question_index.get(quiz_name, 0)
    if current_index >= len(quiz['questions']):
        return redirect(url_for('results', quiz_name=quiz_name, player_name=player_name))

    question = quiz['questions'][current_index]

    return render_template('quiz.html', quiz_name=quiz_name, player_name=player_name, question=question, question_number=current_index + 1)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    quiz_name = request.form.get('quiz_name')
    player_name = request.form.get('player_name')
    answer = request.form.get('answer')

    if quiz_name not in quizzes:
        return "Quiz not found", 404

    quiz = quizzes[quiz_name]
    current_index = current_question_index.get(quiz_name, 0)

    if current_index >= len(quiz['questions']):
        return redirect(url_for('results', quiz_name=quiz_name, player_name=player_name))

    question = quiz['questions'][current_index]

    # Check if the answer is correct
    if answer == question['answer']:
        players[quiz_name][player_name] += 1

    # Move to the next question
    current_question_index[quiz_name] += 1

    return redirect(url_for('quiz', quiz_name=quiz_name, player_name=player_name))

@app.route('/results')
def results():
    quiz_name = request.args.get('quiz_name')
    player_name = request.args.get('player_name')

    if quiz_name not in quizzes:
        return "Quiz not found", 404

    if player_name not in players[quiz_name]:
        return "Player not found", 404

    score = players[quiz_name][player_name]
    return render_template('results.html', score=score, player_name=player_name)

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    quiz_name = request.form.get('quiz_name')
    if quiz_name and quiz_name in quizzes:
        qr_data = url_for('quiz', quiz_name=quiz_name, _external=True)

        # Generate the QR code for the quiz URL
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Save the QR code image in the static folder
        qr_img = qr.make_image(fill='black', back_color='white')
        qr_code_path = os.path.join('static', f'{quiz_name}_qr.png')
        qr_img.save(qr_code_path)

        # Provide the URL of the saved QR code image
        qr_code_url = url_for('static', filename=f'{quiz_name}_qr.png')

        return render_template('quiz_qr.html', qr_code_url=qr_code_url, quiz_name=quiz_name)

    return "Error: Quiz not found!", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

