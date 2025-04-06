from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dlp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

# Database Models
class Classification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), nullable=False)  # Hex color
    description = db.Column(db.Text)

class DocumentLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.Text, nullable=False)
    classification_id = db.Column(db.Integer, db.ForeignKey('classification.id'))
    user = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    action = db.Column(db.String(20), nullable=False)  # create/open/save/reclassify

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin/user

# Create tables
with app.app_context():
    db.create_all()
    # Add default admin if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

# Routes
from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta

@app.route('/')
@app.route('/dashboard')
def dashboard():
    # Get stats for dashboard
    total_docs = DocumentLog.query.count()
    unclassified_docs = DocumentLog.query.filter_by(classification_id=None).count()
    
    # This would be replaced with actual AI detection logic
    sensitive_docs = DocumentLog.query.filter(
        DocumentLog.classification_id.in_([1, 2])  # Assuming 1 and 2 are sensitive classifications
    ).count()
    
    # Get recent activity (last 7 days)
    recent_logs = DocumentLog.query.filter(
        DocumentLog.timestamp >= datetime.now() - timedelta(days=7)
    ).order_by(DocumentLog.timestamp.desc()).limit(10).all()
    
    return render_template('dashboard.html',
                         total_docs=total_docs,
                         unclassified_docs=unclassified_docs,
                         sensitive_docs=sensitive_docs,
                         recent_logs=recent_logs)

@app.route('/classifications')
def classifications():
    classifications = Classification.query.order_by(Classification.id).all()
    return render_template('classifications.html', classifications=classifications)

@app.route('/classifications/add', methods=['POST'])
def add_classification():
    name = request.form.get('name')
    color = request.form.get('color')
    description = request.form.get('description')
    
    if not name or not color:
        flash('Name and color are required', 'error')
        return redirect(url_for('classifications'))
    
    classification = Classification(
        name=name,
        color=color,
        description=description
    )
    db.session.add(classification)
    db.session.commit()
    
    flash('Classification added successfully', 'success')
    return redirect(url_for('classifications'))

@app.route('/classifications/<int:id>/edit', methods=['POST'])
def edit_classification(id):
    classification = Classification.query.get_or_404(id)
    classification.name = request.form.get('name', classification.name)
    classification.color = request.form.get('color', classification.color)
    classification.description = request.form.get('description', classification.description)
    db.session.commit()
    flash('Classification updated successfully', 'success')
    return redirect(url_for('classifications'))

@app.route('/classifications/<int:id>/delete', methods=['POST'])
def delete_classification(id):
    classification = Classification.query.get_or_404(id)
    db.session.delete(classification)
    db.session.commit()
    flash('Classification deleted successfully', 'success')
    return redirect(url_for('classifications'))

@app.route('/logs')
def logs():
    # Get filter parameters
    username = request.args.get('user')
    classification_id = request.args.get('classification')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query
    query = DocumentLog.query
    
    if username:
        query = query.filter(DocumentLog.user == username)
    if classification_id:
        query = query.filter(DocumentLog.classification_id == classification_id)
    if start_date:
        query = query.filter(DocumentLog.timestamp >= start_date)
    if end_date:
        query = query.filter(DocumentLog.timestamp <= end_date)
    
    logs = query.order_by(DocumentLog.timestamp.desc()).all()
    users = User.query.order_by(User.username).all()
    classifications = Classification.query.order_by(Classification.id).all()
    
    return render_template('logs.html',
                         logs=logs,
                         all_users=users,
                         all_classifications=classifications)

if __name__ == '__main__':
    app.run(debug=True)
