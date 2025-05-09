from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import csv
from io import StringIO

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your-email-password'  # Replace with your email password

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # patient, doctor, admin

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    appointment_date = db.Column(db.String(50))
    feedback = db.Column(db.Text)
    feedback_category = db.Column(db.String(100))  # Cleanliness, Staff Behavior, etc.

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    schedule = db.Column(db.String(200))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return render_template('admin_dashboard.html')
    elif current_user.role == 'doctor':
        return render_template('doctor_dashboard.html')
    elif current_user.role == 'patient':
        return render_template('patient_dashboard.html')
    else:
        return redirect(url_for('home'))

@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        appointment_date = request.form['appointment_date']
        new_patient = Patient(name=name, email=email, appointment_date=appointment_date)
        try:
            db.session.add(new_patient)
            db.session.commit()
            # Send appointment notification email
            msg = Message('Appointment Confirmation', sender='your-email@gmail.com', recipients=[email])
            msg.body = f'Dear {name}, your appointment is scheduled for {appointment_date}. Thank you!'
            mail.send(msg)
            flash('Patient added successfully!', 'success')
            return redirect(url_for('patients'))
        except:
            flash('Error adding patient. Please try again.', 'danger')
    patients = Patient.query.all()
    return render_template('patients.html', patients=patients)

@app.route('/doctors', methods=['GET', 'POST'])
@login_required
def doctors():
    if request.method == 'POST':
        name = request.form['name']
        specialization = request.form['specialization']
        schedule = request.form['schedule']
        new_doctor = Doctor(name=name, specialization=specialization, schedule=schedule)
        try:
            db.session.add(new_doctor)
            db.session.commit()
            flash('Doctor added successfully!', 'success')
            return redirect(url_for('doctors'))
        except:
            flash('Error adding doctor. Please try again.', 'danger')
    doctors = Doctor.query.all()
    return render_template('doctors.html', doctors=doctors)

@app.route('/admin/reports')
@login_required
def reports():
    patients = Patient.query.all()
    feedback = [(p.name, p.feedback, p.feedback_category) for p in patients if p.feedback]
    return render_template('reports.html', feedback=feedback)

@app.route('/export-reports')
@login_required
def export_reports():
    patients = Patient.query.all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Name', 'Feedback', 'Category'])
    for p in patients:
        if p.feedback:
            writer.writerow([p.name, p.feedback, p.feedback_category])
    output = si.getvalue()
    si.close()
    return send_file(StringIO(output), mimetype='text/csv', as_attachment=True, download_name='feedback_reports.csv')

# Initialize database
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if not exist
    app.run(debug=True)
