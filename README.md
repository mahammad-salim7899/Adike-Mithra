# 🌱 Adike Mitra - Smart Farming Assistant for Arecanut Farmers

## Project Overview

**Adike Mitra** is a comprehensive web-based platform designed specifically for arecanut farmers in Karnataka and across India. The platform combines artificial intelligence, IoT simulation, weather forecasting, and market analytics to provide farmers with intelligent farming solutions.

### Team Members
- Mahammad Salim
- Mohammad Fawaz
- Shudais Abdul Raheem
- Ibrahim Mohammed Irfaz

## Features

### 🔐 1. User Authentication System
- Secure registration and login
- Two user types: Farmer and Developer (Admin)
- Phone number-based authentication (Indian format)
- Password encryption using Werkzeug

### 🌿 2. Disease Detection Module (AI-Powered)
- **Real Deep Learning Models** trained on 1000+ images
- Upload images of arecanut leaves/fruits
- **97.7% accuracy** for Yellow Leaf Disease detection
- **98.9% accuracy** for Fruit Rot (Koleroga) detection
- Two specialized CNN models with data augmentation
- Disease identification: Yellow Leaf Disease, Fruit Rot, Healthy
- Severity level assessment (mild, moderate, severe)
- Confidence percentage with real predictions
- Treatment recommendations based on AI analysis
- Weather-based spraying advisory
- Complete disease detection history
- **TensorFlow/Keras** powered inference

### 🌦️ 3. Weather-Based Spraying Advisory
- Real-time weather conditions
- 7-day weather forecast
- Smart spraying recommendations
- Risk-level assessment (High, Medium, Low)
- Color-coded calendar view
- Best time suggestions for pesticide application

### 💰 4. Market Price Module
- Live arecanut prices (Red and White varieties)
- Multiple sources (CAMPCO Mangalore, Local Mandi)
- 30-day price trend charts
- Grade-wise pricing (Grade A, B, C)
- Price comparison tools

### 📊 5. Price Prediction
- Historical price analysis (30 days)
- Future price forecasts (15 days)
- Interactive charts with Chart.js
- Statistical insights
- Market trend analysis

### 💧 6. Smart Irrigation System
- Soil moisture simulation
- Remote pump control (ON/OFF)
- Waterlogging detection
- Irrigation activity logs
- Real-time status updates
- Best practices guidance

### 🛠️ 7. Admin Dashboard
- View all users and their activity
- Monitor disease detections across all farmers
- Update market prices manually
- System statistics and analytics
- User management

## Technology Stack

### Backend
- **Python Flask 3.0.0** - Web framework
- **SQLAlchemy 2.0.23** - ORM for database management
- **SQLite** - Database (can be upgraded to PostgreSQL/MySQL)
- **Werkzeug 3.0.1** - Security utilities
- **TensorFlow 2.15.0** - Deep Learning inference for disease detection
- **NumPy 1.26.4** - Numerical computing
- **Pillow 10.2.0** - Image processing

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling with custom green-brown agricultural theme
- **JavaScript** - Interactive features
- **Font Awesome** - Icons
- **Chart.js** - Data visualization

### Machine Learning (NEW!)
- **2 Trained CNN Models** - Real disease detection
- **Yellow Leaf Model** - 97.7% validation accuracy
- **Fruit Rot Model** - 98.9% validation accuracy
- **TensorFlow/Keras** - Model deployment
- **Data Augmentation** - Robust predictions

### Features
- **Responsive Design** - Mobile-friendly interface
- **Farmer-Friendly UI** - Simple, large fonts, icon-based navigation
- **AI-Powered Detection** - Real deep learning models
- **JSON** - API communication and sensor simulation
- **Session Management** - Secure user sessions

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone or Download the Project
```bash
cd "d:\SJEC\V Sem\PBL\Adike Mitra"
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python app.py
```

The application will start on `http://localhost:5000` or `http://127.0.0.1:5000`

### Step 5: Access the Website
Open your web browser and navigate to:
```
http://localhost:5000
```

## First Time Setup

### Register an Account
1. Click on "Register" in the navigation bar
2. Fill in the registration form:
   - **Phone Number**: 10-digit Indian mobile number
   - **Name**: Your full name
   - **Location**: Village/Taluk (e.g., Mangalore, Karnataka)
   - **Farm Size**: Optional (e.g., 5 acres)
   - **User Type**: 
     - Select "Farmer" for regular access
     - Select "Developer" for admin access
   - **Password**: Minimum 6 characters
   - **Confirm Password**: Re-enter your password
3. Click "Register"

### Login
1. Enter your registered phone number
2. Enter your password
3. Click "Login"

### For Farmers
After login, you'll be redirected to the **User Dashboard** where you can:
- View recent disease detections
- Check irrigation logs
- See current market prices
- Access all modules

### For Developers/Admins
After login, you'll be redirected to the **Admin Dashboard** where you can:
- View all registered users
- Monitor all disease detections
- Update market prices
- View system statistics

## Usage Guide

### Disease Detection
1. Go to "Disease Detection" from the dashboard
2. Optionally enter your farm location
3. Upload a clear image of arecanut leaf or fruit
4. Click "Analyze Image"
5. View detection results with recommendations

### Weather Advisory
1. Navigate to "Weather Advisory"
2. View current weather conditions
3. Check 7-day forecast
4. Read smart spraying recommendations
5. Follow the color-coded risk levels

### Market Prices
1. Go to "Market Prices"
2. View current prices for Red and White arecanut
3. Check 30-day price trend chart
4. Compare prices from different sources

### Price Prediction
1. Access "Price Prediction" from Market Prices
2. View historical data (30 days)
3. Check predicted prices (15 days)
4. Analyze market trends

### Smart Irrigation
1. Navigate to "Smart Irrigation"
2. **Control Pump**:
   - Click "Turn ON" to start irrigation
   - Click "Turn OFF" to stop irrigation
3. **Simulate Soil Moisture**:
   - Adjust the slider to simulate moisture level
   - Click "Simulate Reading"
   - View recommendations
4. Check irrigation history log

## Project Structure

```
Adike Mitra/
│
├── app.py                  # Main Flask application
├── models.py               # Database models
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   ├── index.html         # Home page
│   ├── login.html         # Login page
│   ├── register.html      # Registration page
│   ├── user_dashboard.html         # Farmer dashboard
│   ├── admin_dashboard.html        # Admin dashboard
│   ├── disease_detection.html      # Image upload
│   ├── detection_result.html       # Detection results
│   ├── disease_history.html        # Detection history
│   ├── weather_advisory.html       # Weather page
│   ├── market_prices.html          # Market prices
│   ├── price_prediction.html       # Price forecasts
│   └── smart_irrigation.html       # Irrigation control
│
├── static/                # Static files
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   ├── js/
│   │   └── main.js        # JavaScript functions
│   ├── images/            # Image assets
│   └── uploads/           # Uploaded disease images
│
└── database.db            # SQLite database (auto-created)
```

## Database Schema

### Users Table
- `id` - Primary key
- `phone` - Unique phone number (username)
- `name` - Full name
- `location` - Farm location
- `farm_size` - Farm size
- `user_type` - Farmer or Developer
- `password_hash` - Encrypted password
- `created_at` - Registration timestamp

### Disease Detections Table
- `id` - Primary key
- `user_id` - Foreign key to Users
- `image_path` - Path to uploaded image
- `disease_name` - Detected disease
- `severity` - Severity level
- `confidence` - Confidence percentage
- `location` - Detection location
- `detected_at` - Detection timestamp
- `recommendation` - Treatment suggestion
- `weather_warning` - Weather advisory

### Irrigation Logs Table
- `id` - Primary key
- `user_id` - Foreign key to Users
- `soil_moisture` - Moisture percentage
- `pump_status` - ON or OFF
- `action_type` - Manual or Simulation
- `message` - Action message
- `logged_at` - Log timestamp

### Market Prices Table
- `id` - Primary key
- `source` - Price source
- `red_arecanut_price` - Red variety price
- `white_arecanut_price` - White variety price
- `grade` - Quality grade
- `date` - Price date

### Pump Status Table
- `id` - Primary key
- `user_id` - Foreign key to Users
- `status` - Current status (ON/OFF)
- `updated_at` - Last update timestamp

## Default Features

### Sample Data
On first run, the application automatically creates:
- 30 days of sample market price data
- Empty database for users

### Security Features
- Password hashing using Werkzeug
- Session-based authentication
- Login required decorators
- Admin-only route protection
- Input validation
- SQL injection prevention via SQLAlchemy ORM

## Customization

### Adding Real Weather API
Replace the simulated weather data in `app.py` with actual API calls:
```python
# Example: OpenWeatherMap API
import requests
api_key = 'your_api_key'
url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}'
```

### Integrating ML Model for Disease Detection
Replace the random disease detection in `app.py` with your trained model:
```python
# Example: TensorFlow/Keras model
from tensorflow.keras.models import load_model
model = load_model('path_to_model.h5')
prediction = model.predict(processed_image)
```

### Adding Real Market Price API
Connect to actual commodity price APIs for live data

### IoT Sensor Integration
Replace JSON simulation with actual IoT device data:
- Soil moisture sensors
- Water pump controllers
- Weather stations

## Troubleshooting

### Port Already in Use
If port 5000 is busy, change it in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8000)
```

### Database Issues
Delete `database.db` file and restart the application to recreate:
```bash
rm database.db  # Linux/Mac
del database.db  # Windows
python app.py
```

### Import Errors
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt --upgrade
```

## Future Enhancements

- [ ] Integration with real weather APIs
- [ ] Actual ML model for disease detection
- [ ] Real-time IoT sensor data
- [ ] Mobile application (Android/iOS)
- [ ] SMS/Email notifications
- [ ] Multi-language support (Kannada, Hindi, etc.)
- [ ] Export reports as PDF
- [ ] Community forum for farmers
- [ ] Expert consultation booking
- [ ] Crop calendar and reminders
- [ ] Fertilizer recommendations
- [ ] Pest management guide

## License

This project is created for educational purposes as part of a college project.

## Support

For any issues or questions, please contact the development team.

---

**Built with ❤️ for Arecanut Farmers**

**Adike Mitra - Empowering Farmers with Technology** 🌱
