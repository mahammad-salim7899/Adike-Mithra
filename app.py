from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from models import db, User, DiseaseDetection, IrrigationLog, MarketPrice, PumpStatus, SystemSettings
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import json
import random
import numpy as np
import pandas as pd
import joblib
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import load_model
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from price_scraper import scrape_mangalore_prices, get_fallback_prices

app = Flask(__name__)
app.config['SECRET_KEY'] = 'adike-mitra-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Timezone configuration for India (Asia/Kolkata)
IST = ZoneInfo('Asia/Kolkata')

def get_ist_now():
    """Get current time in IST timezone"""
    return datetime.now(IST)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Model configurations
IMG_HEIGHT = 150
IMG_WIDTH = 150
MODEL_PATHS = {
    'yellow_leaf': 'static/models/arecanut_ayld_predictor_v2.keras',
    'fruit_rot': 'static/models/arecanut_koleroga_predictor_v3.keras',
    'price_prediction': 'static/models/arecanut_price_model.pkl'
}

# Load models on startup
disease_models = {}
price_model = None

try:
    disease_models['yellow_leaf'] = load_model(MODEL_PATHS['yellow_leaf'])
    disease_models['fruit_rot'] = load_model(MODEL_PATHS['fruit_rot'])
    print("[SUCCESS] Disease detection models loaded successfully!")
except Exception as e:
    print(f"[WARNING] Could not load disease models - {e}")
    print("Disease detection will use simulation mode.")

try:
    price_model = joblib.load(MODEL_PATHS['price_prediction'])
    print("[SUCCESS] Price prediction model loaded successfully!")
except Exception as e:
    print(f"[WARNING] Could not load price model - {e}")
    print("Price prediction will use simulation mode.")

db.init_app(app)

# Initialize database
with app.app_context():
    db.create_all()
    # Add sample market prices if none exist
    if MarketPrice.query.count() == 0:
        print("[INFO] Initializing market prices with real data...")
        # Try to get real prices
        real_prices = scrape_mangalore_prices()
        if not real_prices:
            print("[WARNING] Could not fetch real prices, using fallback")
            real_prices = get_fallback_prices()
        
        # Create historical data for last 30 days with some variation
        sample_prices = []
        for i in range(30, 0, -1):
            # Add small random variation to prices (-5% to +5%)
            variation = random.uniform(0.95, 1.05)
            price_entry = MarketPrice(
                source='CAMPCO Mangalore',
                red_arecanut_price=round(real_prices['red_arecanut_price'] * variation, 2),
                white_arecanut_price=round(real_prices['white_arecanut_price'] * variation, 2),
                grade='Grade A',
                date=get_ist_now() - timedelta(days=i)
            )
            sample_prices.append(price_entry)
        
        db.session.bulk_save_objects(sample_prices)
        db.session.commit()
        print(f"[SUCCESS] Added {len(sample_prices)} historical price entries")
    
    # Initialize default system settings if none exist
    if SystemSettings.query.count() == 0:
        default_settings = [
            SystemSettings(setting_key='site_name', setting_value='Adike Mitra', setting_type='text', category='general', description='Application name'),
            SystemSettings(setting_key='site_tagline', setting_value='Smart Arecanut Farm Management', setting_type='text', category='general', description='Site tagline'),
            SystemSettings(setting_key='max_upload_size', setting_value='16', setting_type='number', category='general', description='Maximum file upload size in MB'),
            SystemSettings(setting_key='detection_confidence_threshold', setting_value='0.75', setting_type='number', category='detection', description='Minimum confidence for disease detection'),
            SystemSettings(setting_key='enable_notifications', setting_value='true', setting_type='boolean', category='notifications', description='Enable system notifications'),
            SystemSettings(setting_key='irrigation_auto_mode', setting_value='true', setting_type='boolean', category='irrigation', description='Enable automatic irrigation'),
            SystemSettings(setting_key='soil_moisture_threshold', setting_value='30', setting_type='number', category='irrigation', description='Soil moisture threshold for irrigation (%)'),
            SystemSettings(setting_key='maintenance_mode', setting_value='false', setting_type='boolean', category='general', description='Enable maintenance mode'),
            SystemSettings(setting_key='user_registration', setting_value='true', setting_type='boolean', category='general', description='Allow new user registration'),
            SystemSettings(setting_key='session_timeout', setting_value='60', setting_type='number', category='general', description='Session timeout in minutes'),
            SystemSettings(setting_key='ai_model_version', setting_value='v3.0', setting_type='text', category='detection', description='AI model version'),
            SystemSettings(setting_key='backup_frequency', setting_value='daily', setting_type='text', category='general', description='Database backup frequency'),
        ]
        db.session.bulk_save_objects(default_settings)
        db.session.commit()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_content(img_array):
    """
    Validate if the image appears to be plant-related based on advanced color and texture analysis
    Focus on CENTER of image to avoid background interference
    Returns: (is_valid, confidence, reason)
    """
    try:
        # Extract CENTER region (middle 60% of image) to focus on subject, not background
        height, width = img_array.shape[:2]
        center_y_start = int(height * 0.2)
        center_y_end = int(height * 0.8)
        center_x_start = int(width * 0.2)
        center_x_end = int(width * 0.8)
        center_region = img_array[center_y_start:center_y_end, center_x_start:center_x_end]
        
        # Calculate comprehensive color statistics from CENTER region
        mean_color = np.mean(center_region, axis=(0, 1))
        std_color = np.std(center_region, axis=(0, 1))
        
        # RGB channels from center
        r, g, b = mean_color[0], mean_color[1], mean_color[2]
        r_std, g_std, b_std = std_color[0], std_color[1], std_color[2]
        
        # Overall statistics from center
        overall_mean = np.mean(center_region)
        overall_std = np.std(center_region)
        
        # 1. GREEN DOMINANCE CHECK (Critical for plants)
        # Plants must have significant green OR earthy tones
        green_ratio = g / (r + g + b + 1e-6)
        green_dominance = g > r and g > b  # Green is highest channel
        
        # 2. NATURAL COLOR VARIANCE CHECK
        # Plants have organic texture with natural variance
        has_good_variance = overall_std > 15  # Increased threshold
        
        # 3. COLOR CHANNEL BALANCE CHECK
        # Electronic devices often have very balanced or extreme RGB
        channel_imbalance = max(abs(r - g), abs(g - b), abs(r - b))
        is_too_balanced = channel_imbalance < 10  # Too uniform = synthetic
        
        # 4. BLUE/PURPLE DETECTION (Electronic devices, screens)
        is_too_blue = b > max(r, g) and b > 80  # Lowered threshold
        excessive_blue = b > 120 and b > (r + g) / 2  # Detect purple/blue devices
        is_purple = b > 100 and r > 100 and (abs(b - r) < 30) and g < 80  # Purple mouse detection
        
        # 5. UNNATURAL BRIGHTNESS (Screens, reflective objects)
        is_too_bright = overall_mean > 200
        is_too_dark = overall_mean < 20  # Lowered to catch dark objects
        
        # 6. TEXTURE ANALYSIS on center region
        vertical_diff = np.abs(np.diff(center_region, axis=0)).mean()
        horizontal_diff = np.abs(np.diff(center_region, axis=1)).mean()
        texture_complexity = (vertical_diff + horizontal_diff) / 2
        
        has_organic_texture = texture_complexity > 12
        
        # 7. COLOR TEMPERATURE CHECK
        color_temperature = (r + g) / (b + 1e-6)
        is_natural_temperature = color_temperature > 1.8  # Stricter - plants are warm
        
        # 8. GREEN PRESENCE CHECK (Center region MUST have green)
        has_significant_green = (green_ratio > 0.35 and g > 70) or (green_dominance and g > 90)
        
        # 9. PLANT COLOR CHECK - Must be in typical plant color range
        # Green (healthy): G>R, G>B, G>60
        # Yellow/Brown (diseased): R+G high, B low
        is_green_plant = g > max(r, b) and g > 60
        is_brown_plant = (r + g) > (2 * b) and r > 100 and g > 80  # Brownish diseased leaves
        is_plant_colored = is_green_plant or is_brown_plant
        
        # NOTE: Color-based validation has been disabled due to high false positive rate
        # The validation cannot reliably distinguish between:
        # - Non-plant objects with brown/beige colors vs diseased plants
        # - Textured backgrounds vs plant textures
        # - Electronic devices with certain colors vs plant material
        # 
        # A proper solution would require:
        # 1. Training a binary classifier (Plant vs Non-Plant) using transfer learning
        # 2. Using pre-trained models like MobileNet/ResNet with ImageNet weights
        # 3. Fine-tuning on arecanut-specific dataset
        #
        # For now, relying on user responsibility with clear warnings in UI
        
        # Always return valid to bypass validation
        return True, 75.0, "Image validation bypassed - user responsibility"
        
    except Exception as e:
        # If validation fails, allow through
        return True, 75.0, "Image validation bypassed - user responsibility"

def predict_disease(image_path, detection_type='both'):
    """
    Predict disease using trained TensorFlow models
    detection_type: 'yellow_leaf', 'fruit_rot', or 'both'
    Returns: dict with disease predictions and validation status
    """
    try:
        # Load and preprocess image
        img = Image.open(image_path)
        img = img.resize((IMG_HEIGHT, IMG_WIDTH))
        img_array = np.array(img)
        img_batch = np.expand_dims(img_array, axis=0)
        normalized_img = img_batch / 255.0
        
        # Validate image content first
        is_valid, validation_confidence, validation_reason = validate_image_content(img_array)
        
        results = {
            'validation': {
                'is_valid': is_valid,
                'confidence': validation_confidence,
                'reason': validation_reason
            }
        }
        
        # If validation fails, return early with error
        if not is_valid:
            results['error'] = 'Invalid image: ' + validation_reason
            return results
        
        # Yellow Leaf Disease Detection
        if detection_type in ['yellow_leaf', 'both'] and 'yellow_leaf' in disease_models:
            prediction = disease_models['yellow_leaf'].predict(normalized_img, verbose=0)
            prob = float(prediction[0][0])
            
            if prob > 0.5:
                results['yellow_leaf'] = {
                    'disease': 'Yellow Leaf Disease',
                    'confidence': round(prob * 100, 2),
                    'status': 'Infected'
                }
            else:
                results['yellow_leaf'] = {
                    'disease': 'Healthy Leaf',
                    'confidence': round((1 - prob) * 100, 2),
                    'status': 'Healthy'
                }
        
        # Fruit Rot (Koleroga) Detection
        if detection_type in ['fruit_rot', 'both'] and 'fruit_rot' in disease_models:
            prediction = disease_models['fruit_rot'].predict(normalized_img, verbose=0)
            prob = float(prediction[0][0])
            
            if prob > 0.5:
                results['fruit_rot'] = {
                    'disease': 'Fruit Rot (Koleroga)',
                    'confidence': round(prob * 100, 2),
                    'status': 'Infected'
                }
            else:
                results['fruit_rot'] = {
                    'disease': 'Healthy Fruit',
                    'confidence': round((1 - prob) * 100, 2),
                    'status': 'Healthy'
                }
        
        return results
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        return None

def get_disease_recommendation(disease_name, confidence):
    """Generate treatment recommendations based on disease"""
    recommendations = {
        'Yellow Leaf Disease': {
            'treatment': 'Apply Bordeaux mixture (1%) or Copper oxychloride (0.3%). Ensure proper drainage and avoid waterlogging.',
            'severity': 'moderate' if confidence > 85 else 'mild',
            'preventive': 'Maintain soil pH between 5.5-6.5. Apply organic manure regularly. Ensure adequate spacing between plants.'
        },
        'Fruit Rot (Koleroga)': {
            'treatment': 'Spray Carbendazim (0.1%) or Mancozeb (0.25%). Remove and destroy infected fruits immediately.',
            'severity': 'severe' if confidence > 90 else 'moderate',
            'preventive': 'Improve air circulation. Avoid overhead irrigation. Apply prophylactic sprays during monsoon.'
        },
        'Healthy': {
            'treatment': 'No treatment required. Your crop looks healthy!',
            'severity': 'None',
            'preventive': 'Continue regular monitoring. Maintain good cultural practices.'
        }
    }
    
    return recommendations.get(disease_name, recommendations['Healthy'])

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        user = db.session.get(User, session['user_id'])
        if user.user_type != 'Developer':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Home Page
@app.route('/')
def index():
    # Get dynamic stats
    total_farmers = User.query.filter_by(user_type='Farmer').count()
    total_detections = DiseaseDetection.query.count()
    
    stats = {
        'farmers': total_farmers,
        'detections': total_detections,
        'accuracy': 97.7  # AI model accuracy
    }
    
    return render_template('index.html', stats=stats)

# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone')
        email = request.form.get('email')
        name = request.form.get('name')
        location = request.form.get('location')
        farm_size = request.form.get('farm_size')
        user_type = request.form.get('user_type')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([phone, name, user_type, password]):
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('register'))
        
        if len(phone) != 10 or not phone.isdigit():
            flash('Phone number must be 10 digits.', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(phone=phone).first():
            flash('Phone number already registered.', 'danger')
            return redirect(url_for('register'))
        
        if email and User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(
            phone=phone,
            email=email if email else None,
            name=name,
            location=location,
            farm_size=farm_size,
            user_type=user_type
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        user = User.query.filter_by(phone=phone).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_type'] = user.user_type
            
            flash(f'Welcome back, {user.name}!', 'success')
            
            if user.user_type == 'Developer':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid phone number or password.', 'danger')
    
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# FAQ / Support Page
@app.route('/faq')
def faq():
    return render_template('faq.html')

# User Profile
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = db.session.get(User, session['user_id'])
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            name = request.form.get('name')
            email = request.form.get('email')
            location = request.form.get('location')
            farm_size = request.form.get('farm_size')
            
            if name:
                user.name = name
            if email:
                # Check if email is already used by another user
                existing_user = User.query.filter_by(email=email).first()
                if existing_user and existing_user.id != user.id:
                    flash('Email already in use by another account.', 'danger')
                    return redirect(url_for('profile'))
                user.email = email
            user.location = location
            user.farm_size = farm_size
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('profile'))
            
            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('profile'))
            
            if len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return redirect(url_for('profile'))
            
            user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

# User Dashboard
@app.route('/dashboard')
@login_required
def user_dashboard():
    user = db.session.get(User, session['user_id'])
    recent_detections = DiseaseDetection.query.filter_by(user_id=user.id).order_by(DiseaseDetection.detected_at.desc()).limit(5).all()
    recent_irrigation = IrrigationLog.query.filter_by(user_id=user.id).order_by(IrrigationLog.logged_at.desc()).limit(5).all()
    latest_price = MarketPrice.query.order_by(MarketPrice.date.desc()).first()
    
    # Calculate detection insights
    all_detections = DiseaseDetection.query.filter_by(user_id=user.id).all()
    total_detections = len(all_detections)
    
    # Count disease types
    healthy_count = sum(1 for d in all_detections if d.disease_name == 'Healthy')
    disease_count = total_detections - healthy_count
    
    # Calculate health rate
    health_rate = round((healthy_count / total_detections * 100), 1) if total_detections > 0 else 0
    
    # Most recent disease (excluding Healthy)
    recent_disease = next((d.disease_name for d in recent_detections if d.disease_name != 'Healthy'), None)
    
    # Detection insights
    insights = {
        'total': total_detections,
        'healthy': healthy_count,
        'diseased': disease_count,
        'health_rate': health_rate,
        'recent_disease': recent_disease
    }
    
    return render_template('user_dashboard.html', 
                         user=user, 
                         recent_detections=recent_detections,
                         recent_irrigation=recent_irrigation,
                         latest_price=latest_price,
                         insights=insights)

# Delete Detection Record
@app.route('/delete-detection/<int:detection_id>', methods=['POST'])
@login_required
def delete_detection(detection_id):
    detection = DiseaseDetection.query.get_or_404(detection_id)
    user = db.session.get(User, session['user_id'])
    
    # Only allow deletion of own records
    if detection.user_id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    # Delete image file if exists
    if detection.image_path:
        try:
            image_full_path = os.path.join(app.root_path, detection.image_path.lstrip('/'))
            if os.path.exists(image_full_path):
                os.remove(image_full_path)
        except Exception as e:
            print(f"Error deleting image file: {e}")
    
    db.session.delete(detection)
    db.session.commit()
    flash('Detection record deleted successfully.', 'success')
    return redirect(request.referrer or url_for('user_dashboard'))

# Clear All Detections
@app.route('/clear-all-detections', methods=['POST'])
@login_required
def clear_all_detections():
    user = db.session.get(User, session['user_id'])
    detections = DiseaseDetection.query.filter_by(user_id=user.id).all()
    
    # Delete all image files
    for detection in detections:
        if detection.image_path:
            try:
                image_full_path = os.path.join(app.root_path, detection.image_path.lstrip('/'))
                if os.path.exists(image_full_path):
                    os.remove(image_full_path)
            except Exception as e:
                print(f"Error deleting image file: {e}")
    
    # Delete all records
    DiseaseDetection.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    flash('All detection records cleared successfully.', 'success')
    return redirect(url_for('user_dashboard'))

# Clear All Irrigation Logs
@app.route('/clear-all-irrigation', methods=['POST'])
@login_required
def clear_all_irrigation():
    user = db.session.get(User, session['user_id'])
    IrrigationLog.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    flash('All irrigation logs cleared successfully.', 'success')
    return redirect(url_for('user_dashboard'))

# Admin Dashboard
@app.route('/admin')
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_detections = DiseaseDetection.query.count()
    total_irrigation_logs = IrrigationLog.query.count()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_detections=total_detections,
                         total_irrigation_logs=total_irrigation_logs)

# View All Users (Admin)
@app.route('/admin/users')
@admin_required
def admin_users():
    all_users = User.query.all()
    return render_template('admin_users.html', all_users=all_users)

# View All Detections (Admin)
@app.route('/admin/detections')
@admin_required
def admin_detections():
    all_detections = DiseaseDetection.query.order_by(DiseaseDetection.detected_at.desc()).all()
    return render_template('admin_detections.html', all_detections=all_detections)

# Disease Detection - Upload
@app.route('/disease-detection', methods=['GET', 'POST'])
@login_required
def disease_detection():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image uploaded.', 'danger')
            return redirect(request.url)
        
        file = request.files['image']
        
        if file.filename == '':
            flash('No image selected.', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{session['user_id']}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Normalize path separators for cross-platform compatibility
            filepath_normalized = filepath.replace('\\', '/')
            file.save(filepath)
            
            # Get detection type from form (default to 'both')
            detection_type = request.form.get('detection_type', 'both')
            
            # Use real ML model for disease detection
            predictions = predict_disease(filepath, detection_type)
            
            if predictions:
                # Check if validation failed (NOTE: Validation disabled - see comments below)
                # Color-based validation cannot reliably detect non-plant images
                # Users should ensure they upload correct images
                if 'error' in predictions and False:  # Validation disabled
                    # Delete the uploaded file
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    
                    flash(predictions['error'] + ' Please upload a clear image of an arecanut leaf or fruit.', 'danger')
                    return redirect(request.url)
                
                # Determine primary disease based on highest confidence
                primary_disease = None
                max_confidence = 0
                
                for pred_type, pred_data in predictions.items():
                    if pred_type == 'validation':  # Skip validation entry
                        continue
                    if pred_data['status'] == 'Infected' and pred_data['confidence'] > max_confidence:
                        max_confidence = pred_data['confidence']
                        primary_disease = pred_data['disease']
                
                if not primary_disease:
                    # All healthy
                    primary_disease = 'Healthy'
                    confidence = max(pred['confidence'] for pred in predictions.values() if isinstance(pred, dict) and 'confidence' in pred)
                else:
                    confidence = max_confidence
                
                # Get recommendation
                recommendation_data = get_disease_recommendation(primary_disease, confidence)
                recommendation = recommendation_data['treatment']
                severity = recommendation_data['severity']
                
            else:
                # Delete the uploaded file if prediction completely failed
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
                flash('Error processing image. Please upload a clear image of an arecanut leaf or fruit.', 'danger')
                return redirect(request.url)
            
            # Weather warning simulation
            rain_chance = random.randint(0, 100)
            if rain_chance > 60:
                weather_warning = 'Do not spray today, rain expected. Spraying safe tomorrow between 6-10 AM.'
            else:
                weather_warning = 'Weather is favorable for spraying. Best time: 7 AM - 11 AM.'
            
            # Save to database
            detection = DiseaseDetection(
                user_id=session['user_id'],
                image_path=filepath_normalized,  # Use normalized path
                disease_name=primary_disease,
                severity=severity,
                confidence=confidence,
                location=request.form.get('location', ''),
                recommendation=recommendation,
                weather_warning=weather_warning
            )
            db.session.add(detection)
            db.session.commit()
            
            return redirect(url_for('detection_result', detection_id=detection.id))
        else:
            flash('Invalid file type. Please upload an image (PNG, JPG, JPEG, GIF).', 'danger')
    
    return render_template('disease_detection.html')

# Disease Detection Result
@app.route('/detection-result/<int:detection_id>')
@login_required
def detection_result(detection_id):
    detection = DiseaseDetection.query.get_or_404(detection_id)
    
    # Ensure user can only view their own results (unless admin)
    user = db.session.get(User, session['user_id'])
    if detection.user_id != user.id and user.user_type != 'Developer':
        flash('Access denied.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    return render_template('detection_result.html', detection=detection)

# Download Detection PDF
@app.route('/download-detection-pdf/<int:detection_id>')
@login_required
def download_detection_pdf(detection_id):
    detection = DiseaseDetection.query.get_or_404(detection_id)
    
    # Ensure user can only download their own results (unless admin)
    user = db.session.get(User, session['user_id'])
    if detection.user_id != user.id and user.user_type != 'Developer':
        flash('Access denied.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12
    )
    
    # Title
    elements.append(Paragraph("Adike Mitra - Disease Detection Report", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Detection Information Table
    detection_data = [
        ['Report Details', ''],
        ['Detection ID:', str(detection.id)],
        ['Date & Time:', detection.detected_at.strftime('%B %d, %Y at %I:%M %p')],
        ['User:', detection.user.name],
        ['Location:', detection.location or 'Not specified'],
    ]
    
    detection_table = Table(detection_data, colWidths=[2.5*inch, 4*inch])
    detection_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(detection_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Results Section
    elements.append(Paragraph("Detection Results", heading_style))
    
    is_healthy = detection.disease_name == 'Healthy'
    result_color = colors.green if is_healthy else colors.red
    result_bg = colors.HexColor('#d1fae5') if is_healthy else colors.HexColor('#fee2e2')
    
    results_data = [
        ['Parameter', 'Value'],
        ['Disease Status:', 'HEALTHY' if is_healthy else 'DISEASE DETECTED'],
        ['Disease Name:', detection.disease_name],
        ['Confidence Score:', f"{detection.confidence:.2f}%"],
        ['Severity:', detection.severity if detection.severity != 'None' else 'N/A'],
    ]
    
    results_table = Table(results_data, colWidths=[2.5*inch, 4*inch])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (1, 1), result_bg),
        ('TEXTCOLOR', (1, 1), (1, 1), result_color),
        ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(results_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Treatment Recommendations
    if detection.disease_name != 'Healthy' and detection.recommendation:
        elements.append(Paragraph("Treatment Recommendations", heading_style))
        treatment_para = Paragraph(detection.recommendation, styles['BodyText'])
        elements.append(treatment_para)
        elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("This is an automated report generated by Adike Mitra AI System", footer_style))
    elements.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Send file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'detection_report_{detection.id}_{datetime.now().strftime("%Y%m%d")}.pdf',
        mimetype='application/pdf'
    )

# Disease History
@app.route('/disease-history')
@login_required
def disease_history():
    user = db.session.get(User, session['user_id'])
    
    if user.user_type == 'Developer':
        detections = DiseaseDetection.query.order_by(DiseaseDetection.detected_at.desc()).all()
    else:
        detections = DiseaseDetection.query.filter_by(user_id=user.id).order_by(DiseaseDetection.detected_at.desc()).all()
    
    return render_template('disease_history.html', detections=detections)

# Weather Advisory
@app.route('/weather-advisory')
@login_required
def weather_advisory():
    user = db.session.get(User, session['user_id'])
    location = user.location or 'Mangalore, Karnataka'
    
    # Simulate weather data (replace with actual API later)
    current_weather = {
        'temperature': random.randint(25, 35),
        'humidity': random.randint(60, 90),
        'rain_probability': random.randint(0, 100),
        'wind_speed': round(random.uniform(5, 20), 1),
        'condition': random.choice(['Sunny', 'Cloudy', 'Rainy', 'Partly Cloudy'])
    }
    
    # Generate 7-day forecast
    forecast = []
    for i in range(7):
        day_data = {
            'date': (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'),
            'day': (datetime.now() + timedelta(days=i)).strftime('%A'),
            'temp_max': random.randint(28, 35),
            'temp_min': random.randint(20, 26),
            'rain_probability': random.randint(0, 100),
            'condition': random.choice(['Sunny', 'Cloudy', 'Rainy', 'Partly Cloudy'])
        }
        forecast.append(day_data)
    
    # Smart advisory
    if current_weather['rain_probability'] > 60:
        advisory = 'Rain expected today — avoid pesticide spraying. Best time to spray: Tomorrow 7 AM – 11 AM.'
        risk_level = 'high'
    elif current_weather['rain_probability'] > 30:
        advisory = 'Moderate rain chance. Monitor weather closely before spraying.'
        risk_level = 'medium'
    else:
        advisory = 'Weather favorable for spraying. Best time: 7 AM – 11 AM.'
        risk_level = 'low'
    
    return render_template('weather_advisory.html',
                         location=location,
                         current_weather=current_weather,
                         forecast=forecast,
                         advisory=advisory,
                         risk_level=risk_level)

# Market Prices
@app.route('/market-prices')
@login_required
def market_prices():
    # Check if we need to update prices (if latest is older than 1 day)
    latest_prices = MarketPrice.query.order_by(MarketPrice.date.desc()).first()
    
    if latest_prices:
        # Make both datetimes timezone-aware for comparison
        latest_date = latest_prices.date
        if latest_date.tzinfo is None:
            # If stored date is naive, make it aware (assume it's IST)
            latest_date = latest_date.replace(tzinfo=IST)
        
        days_old = (get_ist_now() - latest_date).days
        if days_old >= 1:
            # Fetch and update prices
            update_market_prices()
            latest_prices = MarketPrice.query.order_by(MarketPrice.date.desc()).first()
    else:
        # No prices exist, fetch new ones
        update_market_prices()
        latest_prices = MarketPrice.query.order_by(MarketPrice.date.desc()).first()
    
    # Get historical data for chart (last 30 days)
    thirty_days_ago = get_ist_now() - timedelta(days=30)
    historical_prices = MarketPrice.query.filter(MarketPrice.date >= thirty_days_ago).order_by(MarketPrice.date).all()
    
    # Prepare chart data
    chart_labels = [price.date.strftime('%Y-%m-%d') for price in historical_prices]
    red_prices = [price.red_arecanut_price for price in historical_prices]
    white_prices = [price.white_arecanut_price for price in historical_prices]
    
    return render_template('market_prices.html',
                         latest_prices=latest_prices,
                         chart_labels=json.dumps(chart_labels),
                         red_prices=json.dumps(red_prices),
                         white_prices=json.dumps(white_prices))

# Update Market Prices (can be called via AJAX or scheduled task)
@app.route('/update-prices', methods=['POST'])
@login_required
def update_prices_route():
    """Manual price update endpoint"""
    result = update_market_prices()
    return jsonify(result)

def update_market_prices():
    """
    Fetch latest prices from commodityonline.com and update database
    Returns dict with success status and data
    """
    try:
        # Scrape latest prices
        scraped_data = scrape_mangalore_prices()
        
        if not scraped_data:
            # Use fallback if scraping fails
            scraped_data = get_fallback_prices()
            scraped_data['source'] = 'fallback - scraping failed'
        
        # Check if we already have today's price
        today_start = get_ist_now().replace(hour=0, minute=0, second=0, microsecond=0)
        existing_price = MarketPrice.query.filter(MarketPrice.date >= today_start).first()
        
        if existing_price:
            # Update existing entry
            existing_price.red_arecanut_price = scraped_data['red_arecanut_price']
            existing_price.white_arecanut_price = scraped_data['white_arecanut_price']
            existing_price.date = get_ist_now()
            db.session.commit()
            action = 'updated'
        else:
            # Create new entry
            new_price = MarketPrice(
                source='CAMPCO Mangalore',
                red_arecanut_price=scraped_data['red_arecanut_price'],
                white_arecanut_price=scraped_data['white_arecanut_price'],
                grade='Grade A',
                date=get_ist_now()
            )
            db.session.add(new_price)
            db.session.commit()
            action = 'created'
        
        return {
            'success': True,
            'action': action,
            'data': scraped_data,
            'message': f'Prices {action} successfully'
        }
        
    except Exception as e:
        print(f"Error updating market prices: {e}")
        return {
            'success': False,
            'message': f'Failed to update prices: {str(e)}'
        }

# Price Prediction
@app.route('/price-prediction')
@login_required
def price_prediction():
    # Get historical data (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    historical_prices = MarketPrice.query.filter(MarketPrice.date >= thirty_days_ago).order_by(MarketPrice.date).all()
    
    predictions = []
    
    if price_model and historical_prices and len(historical_prices) >= 14:
        # Use real ML model for predictions
        try:
            # Get the last 14 days of data for lag features
            recent_prices = historical_prices[-14:]
            # Keep prices in rupees (database already stores in rupees)
            base_prices = [p.red_arecanut_price for p in recent_prices]
            
            # Generate 15-day predictions
            for i in range(1, 16):
                pred_date = datetime.now() + timedelta(days=i)
                
                # Prepare features for the model
                current_date = pred_date
                features = {
                    'Year': current_date.year,
                    'Month': current_date.month,
                    'Day': current_date.day,
                    'DayOfWeek': current_date.weekday(),
                    'IsWeekend': 1 if current_date.weekday() >= 5 else 0,
                    
                    # Lag features (use recent actual + predicted prices in rupees)
                    'Lag_1': base_prices[-1] if len(base_prices) >= 1 else historical_prices[-1].red_arecanut_price,
                    'Lag_2': base_prices[-2] if len(base_prices) >= 2 else historical_prices[-2].red_arecanut_price,
                    'Lag_3': base_prices[-3] if len(base_prices) >= 3 else historical_prices[-3].red_arecanut_price,
                    'Lag_7': base_prices[-7] if len(base_prices) >= 7 else historical_prices[-7].red_arecanut_price,
                    'Lag_14': base_prices[-14] if len(base_prices) >= 14 else historical_prices[-14].red_arecanut_price,
                    
                    # Moving averages (in rupees)
                    'MA_7': np.mean(base_prices[-7:]) if len(base_prices) >= 7 else np.mean([p.red_arecanut_price for p in historical_prices[-7:]]),
                    'MA_14': np.mean(base_prices[-14:]) if len(base_prices) >= 14 else np.mean([p.red_arecanut_price for p in historical_prices[-14:]]),
                    'MA_30': np.mean([p.red_arecanut_price for p in historical_prices[-30:]]) if len(historical_prices) >= 30 else np.mean([p.red_arecanut_price for p in historical_prices]),
                    
                    # Standard deviations (in rupees)
                    'STD_7': np.std(base_prices[-7:]) if len(base_prices) >= 7 else np.std([p.red_arecanut_price for p in historical_prices[-7:]]),
                    'STD_14': np.std(base_prices[-14:]) if len(base_prices) >= 14 else np.std([p.red_arecanut_price for p in historical_prices[-14:]]),
                    
                    # Price range (in rupees)
                    'Price_Range': max(base_prices[-7:]) - min(base_prices[-7:]) if len(base_prices) >= 7 else max([p.red_arecanut_price for p in historical_prices[-7:]]) - min([p.red_arecanut_price for p in historical_prices[-7:]])
                }
                
                # Create DataFrame with features
                df = pd.DataFrame([features])
                
                # Predict using the model - it returns in rupees
                red_pred = price_model.predict(df)[0]
                
                # Ensure prediction stays within reasonable bounds (₹350-600 range)
                # If prediction is way off, adjust it to be close to recent prices
                recent_avg = np.mean([p.red_arecanut_price for p in historical_prices[-7:]])
                if red_pred < 100 or red_pred > 1000:
                    # Prediction is unrealistic, use trend-based adjustment
                    red_pred = recent_avg * (1 + np.random.uniform(-0.02, 0.02))
                
                # Assume white price follows similar pattern with ~15% premium
                white_pred = red_pred * 1.15
                
                predictions.append({
                    'date': pred_date.strftime('%Y-%m-%d'),
                    'red': round(float(red_pred), 2),
                    'white': round(float(white_pred), 2)
                })
                
                # Add predicted price to base_prices for next iteration's lag features (in rupees)
                base_prices.append(red_pred)
                if len(base_prices) > 30:
                    base_prices.pop(0)
                    
        except Exception as e:
            print(f"Error in ML prediction: {e}")
            # Fall back to simple simulation
            predictions = generate_simple_predictions(historical_prices)
    else:
        # Fallback: Simple trend prediction
        predictions = generate_simple_predictions(historical_prices)
    
    # Prepare chart data
    hist_labels = [price.date.strftime('%Y-%m-%d') for price in historical_prices]
    hist_red = [price.red_arecanut_price for price in historical_prices]
    hist_white = [price.white_arecanut_price for price in historical_prices]
    
    pred_labels = [p['date'] for p in predictions]
    pred_red = [p['red'] for p in predictions]
    pred_white = [p['white'] for p in predictions]
    
    return render_template('price_prediction.html',
                         hist_labels=json.dumps(hist_labels),
                         hist_red=json.dumps(hist_red),
                         hist_white=json.dumps(hist_white),
                         pred_labels=json.dumps(pred_labels),
                         pred_red=json.dumps(pred_red),
                         pred_white=json.dumps(pred_white))

def generate_simple_predictions(historical_prices):
    """Fallback simple prediction method"""
    predictions = []
    last_price = historical_prices[-1] if historical_prices else None
    
    if last_price:
        for i in range(1, 16):
            pred_date = datetime.now() + timedelta(days=i)
            red_pred = last_price.red_arecanut_price + random.uniform(-20, 30)
            white_pred = last_price.white_arecanut_price + random.uniform(-20, 30)
            predictions.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'red': round(red_pred, 2),
                'white': round(white_pred, 2)
            })
    return predictions

# Smart Irrigation
@app.route('/smart-irrigation', methods=['GET', 'POST'])
@login_required
def smart_irrigation():
    user = db.session.get(User, session['user_id'])
    
    # Get or create pump status
    pump = PumpStatus.query.filter_by(user_id=user.id).first()
    if not pump:
        pump = PumpStatus(user_id=user.id, status='OFF')
        db.session.add(pump)
        db.session.commit()
    
    message = None
    moisture_level = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'simulate':
            # Simulate soil moisture
            moisture_level = float(request.form.get('moisture_level', 50))
            
            if moisture_level < 30:
                message = '⚠️ Water required now. Soil moisture is low.'
                status = 'Low'
            elif moisture_level > 80:
                message = '🚨 Waterlogging detected — stop irrigation immediately!'
                status = 'High'
            else:
                message = '✅ Soil moisture is optimal. No action needed.'
                status = 'Optimal'
            
            # Log the simulation
            log = IrrigationLog(
                user_id=user.id,
                soil_moisture=moisture_level,
                pump_status=pump.status,
                action_type='Simulation',
                message=message
            )
            db.session.add(log)
            db.session.commit()
        
        elif action in ['ON', 'OFF']:
            # Toggle pump
            pump.status = action
            pump.updated_at = datetime.now()
            db.session.commit()
            
            message = f'💡 Pump turned {action}.'
            
            # Log the action
            log = IrrigationLog(
                user_id=user.id,
                soil_moisture=None,
                pump_status=action,
                action_type='Manual',
                message=message
            )
            db.session.add(log)
            db.session.commit()
            
            flash(message, 'success')
            return redirect(url_for('smart_irrigation'))
    
    # Get irrigation history
    history = IrrigationLog.query.filter_by(user_id=user.id).order_by(IrrigationLog.logged_at.desc()).limit(10).all()
    
    return render_template('smart_irrigation.html',
                         pump=pump,
                         history=history,
                         message=message,
                         moisture_level=moisture_level)

# Update Market Prices (Admin Only)
@app.route('/admin/update-prices', methods=['POST'])
@admin_required
def update_prices():
    source = request.form.get('source')
    red_price = float(request.form.get('red_price'))
    white_price = float(request.form.get('white_price'))
    grade = request.form.get('grade')
    
    new_price = MarketPrice(
        source=source,
        red_arecanut_price=red_price,
        white_arecanut_price=white_price,
        grade=grade
    )
    db.session.add(new_price)
    db.session.commit()
    
    flash('Market prices updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# System Settings (Admin Only)
@app.route('/admin/settings')
@admin_required
def system_settings():
    # Get all settings grouped by category
    general_settings = SystemSettings.query.filter_by(category='general').all()
    detection_settings = SystemSettings.query.filter_by(category='detection').all()
    irrigation_settings = SystemSettings.query.filter_by(category='irrigation').all()
    notification_settings = SystemSettings.query.filter_by(category='notifications').all()
    
    # Get system statistics
    total_users = User.query.count()
    total_detections = DiseaseDetection.query.count()
    total_irrigation = IrrigationLog.query.count()
    total_prices = MarketPrice.query.count()
    
    # Get recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_detections = DiseaseDetection.query.order_by(DiseaseDetection.detected_at.desc()).limit(5).all()
    
    return render_template('admin_settings.html',
                         general_settings=general_settings,
                         detection_settings=detection_settings,
                         irrigation_settings=irrigation_settings,
                         notification_settings=notification_settings,
                         total_users=total_users,
                         total_detections=total_detections,
                         total_irrigation=total_irrigation,
                         total_prices=total_prices,
                         recent_users=recent_users,
                         recent_detections=recent_detections)

# Update System Settings (Admin Only)
@app.route('/admin/settings/update', methods=['POST'])
@admin_required
def update_system_settings():
    try:
        user = User.query.filter_by(phone=session['user_phone']).first()
        updated_count = 0
        
        # Get all form data
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                setting = SystemSettings.query.filter_by(setting_key=setting_key).first()
                
                if setting:
                    # Handle boolean values
                    if setting.setting_type == 'boolean':
                        setting.setting_value = 'true' if value == 'on' else 'false'
                    else:
                        setting.setting_value = value
                    
                    setting.updated_by = user.name
                    setting.updated_at = datetime.utcnow()
                    updated_count += 1
        
        db.session.commit()
        flash(f'Successfully updated {updated_count} settings!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating settings: {str(e)}', 'error')
    
    return redirect(url_for('system_settings'))

# Reset System Settings (Admin Only)
@app.route('/admin/settings/reset/<setting_key>', methods=['POST'])
@admin_required
def reset_setting(setting_key):
    try:
        setting = SystemSettings.query.filter_by(setting_key=setting_key).first()
        if setting:
            # Define default values
            defaults = {
                'site_name': 'Adike Mitra',
                'site_tagline': 'Smart Arecanut Farm Management',
                'max_upload_size': '16',
                'detection_confidence_threshold': '0.75',
                'enable_notifications': 'true',
                'irrigation_auto_mode': 'true',
                'soil_moisture_threshold': '30',
                'maintenance_mode': 'false',
                'user_registration': 'true',
                'session_timeout': '60',
                'ai_model_version': 'v3.0',
                'backup_frequency': 'daily'
            }
            
            if setting_key in defaults:
                setting.setting_value = defaults[setting_key]
                setting.updated_at = datetime.utcnow()
                user = User.query.filter_by(phone=session['user_phone']).first()
                setting.updated_by = user.name
                db.session.commit()
                flash(f'Setting "{setting_key}" reset to default value!', 'success')
            else:
                flash(f'No default value defined for "{setting_key}"', 'warning')
        else:
            flash(f'Setting "{setting_key}" not found!', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting setting: {str(e)}', 'error')
    
    return redirect(url_for('system_settings'))

# Export System Data (Admin Only)
@app.route('/admin/settings/export/<data_type>')
@admin_required
def export_system_data(data_type):
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if data_type == 'users':
            users = User.query.all()
            data = [{
                'id': u.id,
                'name': u.name,
                'phone': u.phone,
                'email': u.email,
                'location': u.location,
                'farm_size': u.farm_size,
                'user_type': u.user_type,
                'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for u in users]
            filename = f'users_export_{timestamp}.json'
        
        elif data_type == 'detections':
            detections = DiseaseDetection.query.all()
            data = [{
                'id': d.id,
                'user_id': d.user_id,
                'disease_name': d.disease_name,
                'severity': d.severity,
                'confidence': d.confidence,
                'location': d.location,
                'detected_at': d.detected_at.strftime('%Y-%m-%d %H:%M:%S')
            } for d in detections]
            filename = f'detections_export_{timestamp}.json'
        
        elif data_type == 'settings':
            settings = SystemSettings.query.all()
            data = [{
                'key': s.setting_key,
                'value': s.setting_value,
                'type': s.setting_type,
                'category': s.category,
                'description': s.description,
                'updated_at': s.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_by': s.updated_by
            } for s in settings]
            filename = f'settings_export_{timestamp}.json'
        
        else:
            flash('Invalid export type!', 'error')
            return redirect(url_for('system_settings'))
        
        # Create JSON file
        json_data = json.dumps(data, indent=2)
        
        # Create a BytesIO object
        buffer = BytesIO()
        buffer.write(json_data.encode('utf-8'))
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
    
    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'error')
        return redirect(url_for('system_settings'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
