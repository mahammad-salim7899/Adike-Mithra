from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# India Standard Time
IST = ZoneInfo('Asia/Kolkata')

def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    farm_size = db.Column(db.String(50))
    user_type = db.Column(db.String(20), nullable=False)  # 'Farmer' or 'Developer'
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=get_ist_now)
    
    # Relationships
    disease_detections = db.relationship('DiseaseDetection', backref='user', lazy=True)
    irrigation_logs = db.relationship('IrrigationLog', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.name} - {self.user_type}>'


class DiseaseDetection(db.Model):
    __tablename__ = 'disease_detections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_path = db.Column(db.String(300), nullable=False)
    disease_name = db.Column(db.String(100))
    severity = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    location = db.Column(db.String(200))
    detected_at = db.Column(db.DateTime, default=get_ist_now)
    recommendation = db.Column(db.Text)
    weather_warning = db.Column(db.Text)
    
    def __repr__(self):
        return f'<DiseaseDetection {self.disease_name} - {self.detected_at}>'


class IrrigationLog(db.Model):
    __tablename__ = 'irrigation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    soil_moisture = db.Column(db.Float)
    pump_status = db.Column(db.String(10))  # 'ON' or 'OFF'
    action_type = db.Column(db.String(50))  # 'Manual' or 'Auto'
    message = db.Column(db.Text)
    logged_at = db.Column(db.DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f'<IrrigationLog {self.pump_status} - {self.logged_at}>'


class MarketPrice(db.Model):
    __tablename__ = 'market_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100))  # 'CAMPCO Mangalore', 'Local Mandi', etc.
    red_arecanut_price = db.Column(db.Float)
    white_arecanut_price = db.Column(db.Float)
    grade = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f'<MarketPrice {self.source} - {self.date}>'


class PumpStatus(db.Model):
    __tablename__ = 'pump_status'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(10), default='OFF')  # 'ON' or 'OFF'
    updated_at = db.Column(db.DateTime, default=get_ist_now, onupdate=get_ist_now)
    
    def __repr__(self):
        return f'<PumpStatus {self.status}>'


class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    setting_type = db.Column(db.String(50))  # 'text', 'number', 'boolean', 'json'
    category = db.Column(db.String(100))  # 'general', 'detection', 'irrigation', 'notifications'
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=get_ist_now, onupdate=get_ist_now)
    updated_by = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<SystemSettings {self.setting_key}={self.setting_value}>'
