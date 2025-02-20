from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import wraps
from datetime import datetime
import os

# Ensure the persistent directory exists for SQLite storage
if not os.path.exists('/data'):
    os.makedirs('/data', exist_ok=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'  # Change to a secure key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/outage.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Hardcoded admin credentials (update for production)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'

# Define a folder to store the PDFs
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Models
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # status should be "up" or "down" (you could extend this if needed)
    status = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Add this line

class OutageReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    report_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # create a relationship so you can easily get the service details
    service = db.relationship('Service', backref=db.backref('reports', lazy=True))

# Decorator to protect admin routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in as admin to access that page.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Public outage board page
@app.route('/')
def index():
    services = Service.query.all()
    # Get list of PDFs from the upload folder
    pdf_files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.lower().endswith('.pdf'):
            pdf_files.append(filename)
    return render_template('index.html', services=services, pdf_files=pdf_files)


@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'message': 'File successfully uploaded', 'filename': filename}), 200
    else:
        return jsonify({'error': 'Allowed file type is pdf'}), 400


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route for reporting an outage on a specific service
@app.route('/report/<int:service_id>', methods=['GET', 'POST'])
def report(service_id):
    service = Service.query.get_or_404(service_id)
    if request.method == 'POST':
        report_text = request.form.get('report_text')
        if report_text:
            new_report = OutageReport(service_id=service.id, report_text=report_text)
            db.session.add(new_report)
            db.session.commit()
            flash('Report submitted successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Please enter a report.', 'danger')
    return render_template('report.html', service=service)

# Admin login page
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('admin_login.html')

# Admin logout
@app.route('/admin/logout')
@admin_required
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# Admin dashboard to view and manage services and reports
@app.route('/admin')
@admin_required
def admin_dashboard():
    services = Service.query.all()
    reports = OutageReport.query.order_by(OutageReport.timestamp.desc()).all()
    return render_template('admin_dashboard.html', services=services, reports=reports)

# Admin route to add a new service
@app.route('/admin/service/add', methods=['GET', 'POST'])
@admin_required
def add_service():
    if request.method == 'POST':
        name = request.form.get('name')
        status = request.form.get('status')
        description = request.form.get('description')  # Add this line
        if name and status:
            new_service = Service(name=name, status=status, description=description)  # Include description here
            db.session.add(new_service)
            db.session.commit()
            flash('Service added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('All fields are required.', 'danger')
    return render_template('add_service.html')

# Admin route to edit an existing service
@app.route('/admin/service/edit/<int:service_id>', methods=['GET', 'POST'])
@admin_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    if request.method == 'POST':
        service.name = request.form.get('name')
        service.status = request.form.get('status')
        service.description = request.form.get('description')  # Add this line
        db.session.commit()
        flash('Service updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_service.html', service=service)

# Ensure the database is created when running with Gunicorn
@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    # Create the SQLite database and tables if they don't exist.
    with app.app_context():
        db.create_all()
    app.run(debug=True)
