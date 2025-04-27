from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///training.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Base model for exercises
class Exercise(db.Model):
    __tablename__ = 'exercises'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    sport = db.Column(db.String(50), nullable=False)
    details = db.Column(db.JSON, nullable=False)  # Stores exercise-specific attributes
    calories_burned = db.Column(db.Float, nullable=False)  # Stores calories burned

    def __repr__(self):
        return f"<Exercise {self.sport} on {self.date}>"

# Helper class for input validation and processing
class ExerciseFactory:
    # Calorie burn rate per minute or per repetition based on sport
    CALORIE_BURN_RATE = {
        'running': 10,      # calories per minute
        'swimming': 12,     # calories per minute
        'cycling': 8,       # calories per minute
        'pullups': 0.5,     # calories per repetition
        'pushups': 0.5,     # calories per repetition
        'weights': 0.6      # calories per repetition
    }

    @staticmethod
    def create_exercise(sport, data):
        if sport not in ExerciseFactory.CALORIE_BURN_RATE:
            raise ValueError("Unsupported sport type")

        validators = {
            'running': ExerciseFactory.validate_running,
            'swimming': ExerciseFactory.validate_swimming,
            'pullups': ExerciseFactory.validate_pullups,
            'cycling': ExerciseFactory.validate_cycling,
            'pushups': ExerciseFactory.validate_pushups,
            'weights': ExerciseFactory.validate_weights,
        }

        validated_data = validators[sport](data)
        validated_data['calories_burned'] = ExerciseFactory.calculate_calories(sport, validated_data)
        return validated_data

    @staticmethod
    def validate_running(data):
        if 'time' not in data or 'distance' not in data:
            raise ValueError("Running requires 'time' and 'distance'")
        return {'time': data['time'], 'distance': data['distance']}

    @staticmethod
    def validate_swimming(data):
        if 'time' not in data or 'distance' not in data:
            raise ValueError("Swimming requires 'time' and 'distance'")
        return {'time': data['time'], 'distance': data['distance']}

    @staticmethod
    def validate_pullups(data):
        if 'sets' not in data or 'reps_per_set' not in data:
            raise ValueError("Pull-ups require 'sets' and 'reps_per_set'")
        return {'sets': data['sets'], 'reps_per_set': data['reps_per_set']}

    @staticmethod
    def validate_cycling(data):
        if 'time' not in data or 'distance' not in data:
            raise ValueError("Cycling requires 'time' and 'distance'")
        return {'time': data['time'], 'distance': data['distance']}

    @staticmethod
    def validate_pushups(data):
        if 'sets' not in data or 'reps_per_set' not in data:
            raise ValueError("Push-ups require 'sets' and 'reps_per_set'")
        return {'sets': data['sets'], 'reps_per_set': data['reps_per_set']}

    @staticmethod
    def validate_weights(data):
        if 'exercise_type' not in data or 'sets' not in data or 'reps_per_set' not in data:
            raise ValueError("Weights require 'exercise_type', 'sets', and 'reps_per_set'")
        return {
            'exercise_type': data['exercise_type'],
            'sets': data['sets'],
            'reps_per_set': data['reps_per_set']
        }

    @staticmethod
    def calculate_calories(sport, data):
        rate = ExerciseFactory.CALORIE_BURN_RATE[sport]
        if sport in ['running', 'swimming', 'cycling']:
            return data['time'] * rate  # time in minutes
        elif sport in ['pullups', 'pushups', 'weights']:
            total_reps = data['sets'] * data['reps_per_set']
            return total_reps * rate  # repetitions
        else:
            return 0

# API Routes
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Training Tracker API! Use /add to add data and /get to view records."}), 200

@app.route('/add', methods=['POST'])
def add_exercise():
    try:
        data = request.json
        sport = data.get('sport')
        exercise_data = ExerciseFactory.create_exercise(sport, data)

        new_exercise = Exercise(sport=sport, details=exercise_data, calories_burned=exercise_data['calories_burned'])
        db.session.add(new_exercise)
        db.session.commit()

        return jsonify({"message": "Exercise added successfully!", "exercise": new_exercise.details, "calories_burned": new_exercise.calories_burned}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

@app.route('/get', methods=['GET'])
def get_exercises():
    try:
        exercises = Exercise.query.all()
        result = [
            {
                "id": exercise.id,
                "date": exercise.date.strftime('%Y-%m-%d'),
                "sport": exercise.sport,
                "details": exercise.details,
                "calories_burned": exercise.calories_burned
            } for exercise in exercises
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
