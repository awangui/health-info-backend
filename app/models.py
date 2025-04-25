# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Association table for many-to-many relationship between clients and health programs
client_programs = db.Table('client_programs',
    db.Column('client_id', db.Integer, db.ForeignKey('clients.id'), primary_key=True),
    db.Column('program_id', db.Integer, db.ForeignKey('health_programs.id'), primary_key=True),
    db.Column('enrollment_date', db.DateTime, default=datetime.now),
    db.Column('notes', db.Text)
)

class HealthProgram(db.Model):
    __tablename__ = 'health_programs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # e.g., "TB", "Malaria"
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)  
    
    clients = db.relationship('Client', secondary=client_programs, back_populates='programs')

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now) 
    programs = db.relationship('HealthProgram', secondary=client_programs, back_populates='clients')
