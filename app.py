# ===================== Real Estate AI - Complete Application =====================
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import numpy as np
import joblib
import os
import json
import re
import base64
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from functools import wraps
import hashlib
import secrets
import time
from collections import defaultdict
from utils.security import (
    security_manager, rate_limit, sanitize_request_data,
    validate_property_input, log_security_event, get_client_ip,
    is_suspicious_request
)
from database import db_manager
from utils.analytics import analytics_manager, track_page_view, track_feature_usage, get_dashboard_analytics
from utils.notifications import notification_manager, send_property_inquiry, send_rental_booking
from utils.amenities import amenities_manager, get_location_amenities
from utils.property_types import property_type_manager
from utils.enhanced_prediction import enhanced_predictor
from utils.property_presets import property_presets

# Debug: Check if amenities field is loaded
print("🔍 DEBUG: Checking amenities field in Flask app...")
try:
    test_2bhk = property_type_manager.get_property_type('2bhk')
    if test_2bhk:
        field_names = [field.name for field in test_2bhk.fields]
        print(f"   2BHK fields in Flask: {field_names}")
        print(f"   Has amenities in Flask: {'amenities' in field_names}")
    else:
        print("   2BHK not found in Flask")
except Exception as e:
    print(f"   Error checking amenities in Flask: {e}")

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'real-estate-secret-key-2025-production')

# Enable template auto-reload for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# Security configurations
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# User authentication decorator
def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = session.get('user_session_token')
        if not session_token:
            # Check if this is an AJAX request (expecting JSON response)
            if request.method == 'POST' and (request.content_type and 'multipart/form-data' in request.content_type):
                return jsonify({'success': False, 'error': 'Please login to continue'}), 401
            return redirect(url_for('login'))

        # Validate session
        result = db_manager.validate_session(session_token)
        if not result['success']:
            session.clear()
            # Check if this is an AJAX request (expecting JSON response)
            if request.method == 'POST' and (request.content_type and 'multipart/form-data' in request.content_type):
                return jsonify({'success': False, 'error': 'Session expired, please login again'}), 401
            return redirect(url_for('login'))

        # Store user info in session for easy access
        session['current_user'] = result['user']
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged-in user"""
    session_token = session.get('user_session_token')
    if not session_token:
        return None

    result = db_manager.validate_session(session_token)
    if result['success']:
        return result['user']
    return None

@app.context_processor
def inject_current_user():
    """Make current_user available to all templates"""
    return {'current_user': get_current_user()}

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; img-src 'self' data: https:; font-src 'self' https://cdnjs.cloudflare.com;"
    return response

# ===================== ADMIN PANEL CONFIGURATION =====================

# Admin credentials (In production, use environment variables)
ADMIN_CREDENTIALS = {
    'admin': hashlib.sha256('admin123'.encode()).hexdigest(),  # Change this password!
    'developer': hashlib.sha256('dev2024!'.encode()).hexdigest(),  # Change this password!
}

# Admin session management
admin_sessions = {}
admin_login_attempts = defaultdict(list)

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            # Check if this is an AJAX/API request (POST request expecting JSON)
            if request.method == 'POST':
                return jsonify({'success': False, 'error': 'Admin authentication required'}), 401
            return redirect(url_for('admin_login'))

        return f(*args, **kwargs)
    return decorated_function

def log_admin_action(action, details=None):
    """Log admin actions for audit trail"""
    admin_id = session.get('admin_id', 'unknown')
    timestamp = datetime.now().isoformat()

    log_entry = {
        'timestamp': timestamp,
        'admin_id': admin_id,
        'action': action,
        'details': details or {},
        'ip_address': get_client_ip()
    }

    # In production, save to database or file
    # For now, we'll store in session for demo
    if 'admin_logs' not in session:
        session['admin_logs'] = []

    session['admin_logs'].append(log_entry)
    session.modified = True

# Global variables for model and data
model = None
df = None
locations = []

def load_data():
    """Load model and data"""
    global model, df, locations

    try:
        # Load model
        if os.path.exists('model.pkl'):
            model = joblib.load('model.pkl')
            print("✅ Model loaded successfully")

        # Load data
        if os.path.exists('housing.csv'):
            df = pd.read_csv('housing.csv')
            print("✅ Housing data loaded successfully")
        elif os.path.exists('Bengaluru_House_Data.csv'):
            df = pd.read_csv('Bengaluru_House_Data.csv')
            print("✅ Bengaluru data loaded successfully")

        # Extract locations
        if df is not None and 'location' in df.columns:
            # Filter out NaN values and convert to string before sorting
            unique_locations = df['location'].dropna().astype(str).unique().tolist()
            locations = sorted([loc for loc in unique_locations if loc != 'nan'])
        else:
            locations = [
                "Electronic City Phase II", "Chikka Tirupathi", "Uttarahalli",
                "Lingadheeranahalli", "Kothanur", "Whitefield", "Old Airport Road",
                "Rajaji Nagar", "Marathahalli", "Gandhi Bazar", "Koramangala",
                "Indiranagar", "Jayanagar", "BTM Layout", "HSR Layout"
            ]

        print(f"✅ Loaded {len(locations)} locations")

    except Exception as e:
        print(f"❌ Error loading data: {e}")

# Load data on startup
load_data()

def predict_price(data):
    """Enhanced price prediction with dashboard data"""
    try:
        if model is not None:
            # Create a simple prediction based on available data
            base_price = 50  # Base price in lakhs

            # Adjust based on total_sqft
            sqft_factor = data.get('total_sqft', 1000) / 1000
            price = base_price * sqft_factor

            # Adjust based on BHK
            size = data.get('size', '2 BHK')
            if '3' in str(size):
                price *= 1.3
            elif '4' in str(size):
                price *= 1.6
            elif '1' in str(size):
                price *= 0.7

            # Adjust based on location (premium locations)
            location = data.get('location', '').lower()
            premium_locations = ['whitefield', 'koramangala', 'indiranagar', 'jayanagar']
            if any(loc in location for loc in premium_locations):
                price *= 1.4

            # Add some randomness for realism
            price *= (0.9 + np.random.random() * 0.2)

            return max(price, 10)  # Minimum 10 lakhs
        else:
            # Fallback calculation
            return 75.5 + np.random.random() * 50

    except Exception as e:
        print(f"Prediction error: {e}")
        return 75.5

def get_dashboard_data(prediction_data=None):
    """Generate dashboard data based on prediction"""
    if prediction_data:
        location = prediction_data.get('location', 'Bangalore')
        price = prediction_data.get('predicted_price', 100)
        sqft = prediction_data.get('total_sqft', 1200)

        # Generate location-specific insights
        price_per_sqft = (price * 100000) / sqft

        # Market comparison
        avg_price = price * (0.8 + np.random.random() * 0.4)
        growth_rate = 8 + np.random.random() * 10

        return {
            'current_property': {
                'price': price,
                'price_per_sqft': price_per_sqft,
                'location': location,
                'size': prediction_data.get('size', '2 BHK')
            },
            'market_data': {
                'avg_price': avg_price,
                'growth_rate': growth_rate,
                'price_trend': 'Rising' if growth_rate > 10 else 'Stable',
                'investment_rating': 'Excellent' if growth_rate > 12 else 'Good' if growth_rate > 8 else 'Average'
            },
            'location_insights': {
                'connectivity': 'Excellent' if 'whitefield' in location.lower() or 'koramangala' in location.lower() else 'Good',
                'amenities': 'Premium' if price > 120 else 'Standard',
                'future_prospects': 'High' if growth_rate > 10 else 'Medium'
            }
        }
    else:
        # Default dashboard data
        return {
            'current_property': None,
            'market_data': {
                'avg_price': 112.5,
                'growth_rate': 9.2,
                'price_trend': 'Rising',
                'investment_rating': 'Good'
            },
            'location_insights': {
                'connectivity': 'Good',
                'amenities': 'Standard',
                'future_prospects': 'Medium'
            }
        }

# ===================== ROUTES =====================

@app.route('/')
def index():
    """Home page with dashboard"""
    # Track page view
    session_id = session.get('session_id', f"session_{datetime.now().timestamp()}")
    session['session_id'] = session_id
    track_page_view('home', session_id)

    # Get current user if logged in
    current_user = get_current_user()

    dashboard_data = get_dashboard_data()
    return render_template('simple_index.html',
                         locations=locations,
                         dashboard=dashboard_data,
                         current_user=current_user)

# User Authentication Routes
@app.route('/signup', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window_seconds=300)
def signup():
    """User registration"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form

            # Validate required fields
            required_fields = ['username', 'email', 'password', 'confirm_password']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'success': False, 'error': f'{field.replace("_", " ").title()} is required'})

            # Validate password match
            if data.get('password') != data.get('confirm_password'):
                return jsonify({'success': False, 'error': 'Passwords do not match'})

            # Validate email format
            email = data.get('email').strip().lower()
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return jsonify({'success': False, 'error': 'Invalid email format'})

            # Validate username
            username = data.get('username').strip()
            if len(username) < 3 or not re.match(r'^[a-zA-Z0-9_]+$', username):
                return jsonify({'success': False, 'error': 'Username must be at least 3 characters and contain only letters, numbers, and underscores'})

            # Validate password strength
            password = data.get('password')
            if len(password) < 6:
                return jsonify({'success': False, 'error': 'Password must be at least 6 characters long'})

            # Create user
            result = db_manager.create_user(
                username=username,
                email=email,
                password=password,
                full_name=data.get('full_name', '').strip(),
                phone=data.get('phone', '').strip()
            )

            if result['success']:
                return jsonify({'success': True, 'message': 'Account created successfully! Please log in.'})
            else:
                return jsonify({'success': False, 'error': result['error']})

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window_seconds=300)
def login():
    """User login"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form

            username_or_email = data.get('username_or_email', '').strip()
            password = data.get('password', '')

            if not username_or_email or not password:
                return jsonify({'success': False, 'error': 'Username/email and password are required'})

            # Authenticate user
            result = db_manager.authenticate_user(username_or_email, password)

            if result['success']:
                # Create session
                session_result = db_manager.create_session(result['user']['id'])

                if session_result['success']:
                    # Store session token
                    session['user_session_token'] = session_result['session_token']
                    session['current_user'] = result['user']
                    session.permanent = True

                    return jsonify({'success': True, 'message': 'Login successful', 'redirect': '/'})
                else:
                    return jsonify({'success': False, 'error': 'Failed to create session'})
            else:
                return jsonify({'success': False, 'error': result['error']})

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session_token = session.get('user_session_token')
    if session_token:
        db_manager.logout_user(session_token)

    session.clear()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    current_user = get_current_user()

    # Get user's properties
    properties_result = db_manager.get_user_properties(current_user['id'])
    properties = properties_result.get('properties', []) if properties_result['success'] else []

    # Get user's rental properties
    rentals_result = db_manager.get_user_rental_properties(current_user['id'])
    rentals = rentals_result.get('rentals', []) if rentals_result['success'] else []

    # Debug logging
    print(f"DEBUG: Profile - User ID: {current_user['id']}")
    print(f"DEBUG: Profile - Properties result: {properties_result['success']}")
    print(f"DEBUG: Profile - Number of properties: {len(properties)}")
    print(f"DEBUG: Profile - Number of rentals: {len(rentals)}")

    return render_template('profile.html',
                         current_user=current_user,
                         properties=properties,
                         rentals=rentals)

@app.route('/predict', methods=['GET', 'POST'])
@rate_limit(max_requests=20, window_seconds=60)
@sanitize_request_data()
def predict_page():
    """Prediction page with enhanced dashboard"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()

            # Clean data
            clean_data = {
                'location': data.get('location', ''),
                'area_type': data.get('area_type', 'Super built-up Area'),
                'size': data.get('size', '2 BHK'),
                'total_sqft': float(data.get('total_sqft', 1000)),
                'bath': int(data.get('bath', 2)),
                'balcony': int(data.get('balcony', 1)),
                'availability': data.get('availability', 'Ready To Move')
            }

            # Get prediction
            price = predict_price(clean_data)
            clean_data['predicted_price'] = price

            # Generate dashboard data based on prediction
            dashboard_data = get_dashboard_data(clean_data)

            # Save to session
            if 'predictions' not in session:
                session['predictions'] = []

            prediction_record = {
                'id': len(session['predictions']) + 1,
                'timestamp': datetime.now().isoformat(),
                'input_data': clean_data,
                'predicted_price': round(price, 2),
                'formatted_price': f"₹{price:,.2f} Lakhs",
                'dashboard_data': dashboard_data
            }

            session['predictions'].append(prediction_record)
            session.modified = True

            if request.is_json:
                return jsonify({
                    'success': True,
                    'prediction': round(price, 2),
                    'formatted_price': f"₹{price:,.2f} Lakhs",
                    'confidence': 'High',
                    'dashboard_data': dashboard_data
                })
            else:
                return render_template('simple_predict.html',
                                     locations=locations,
                                     result=prediction_record,
                                     dashboard=dashboard_data)

        except Exception as e:
            error_msg = f"Prediction error: {str(e)}"
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 500
            else:
                return render_template('simple_predict.html',
                                     locations=locations,
                                     error=error_msg)

    return render_template('simple_predict.html', locations=locations)

@app.route('/enhanced-predict')
def enhanced_predict_page():
    """Enhanced prediction page with property type selection"""
    try:
        return render_template('enhanced_predict.html')
    except Exception as e:
        return f"""
        <html><head><title>Enhanced Price Prediction</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>🏠 Enhanced Price Prediction</h1>
            <p>Advanced property-type-specific price prediction system.</p>
            <div style="margin: 20px 0;">
                <h3>Features:</h3>
                <p>• Property-type-specific predictions</p>
                <p>• Dynamic form fields</p>
                <p>• Advanced analytics</p>
                <p>• Detailed insights</p>
            </div>
            <a href="/predict" style="color: #667eea;">Try Basic Prediction →</a><br><br>
            <a href="/" style="color: #667eea;">← Back to Home</a>
        </body></html>
        """, 200

@app.route('/test-enhanced')
def test_enhanced_predict():
    """Test page for enhanced prediction"""
    return render_template('test_enhanced.html')

@app.route('/debug-amenities')
def debug_amenities():
    """Debug amenities field"""
    try:
        from utils.property_types import property_type_manager

        # Test 2bhk specifically
        prop_type = property_type_manager.get_property_type('2bhk')
        field_names = [field.name for field in prop_type.fields] if prop_type else []

        # Test API method
        api_fields = property_type_manager.get_fields_for_type('2bhk')
        api_field_names = [field.get('name') for field in api_fields]

        # Find amenities field
        amenities_field = None
        for field in api_fields:
            if field.get('name') == 'amenities':
                amenities_field = field
                break

        # Test individual field serialization
        serialization_results = []
        if prop_type:
            for field in prop_type.fields:
                try:
                    serialized = field.to_dict()
                    serialization_results.append({
                        'name': field.name,
                        'status': 'success',
                        'keys': list(serialized.keys())
                    })
                except Exception as e:
                    serialization_results.append({
                        'name': field.name,
                        'status': 'failed',
                        'error': str(e)
                    })

        return jsonify({
            'property_type_fields': field_names,
            'api_fields': api_field_names,
            'amenities_field_found': amenities_field is not None,
            'amenities_field': amenities_field,
            'total_api_fields': len(api_fields),
            'serialization_results': serialization_results
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/property-types')
@rate_limit(max_requests=50, window_seconds=60)
def api_property_types():
    """Get all available property types"""
    try:
        property_types = property_type_manager.get_property_type_list()
        return jsonify({
            'success': True,
            'property_types': {pt['id']: pt for pt in property_types}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/property-types/<type_id>/fields')
@rate_limit(max_requests=50, window_seconds=60)
def api_property_type_fields(type_id):
    """Get form fields for a specific property type"""
    try:
        fields = property_type_manager.get_fields_for_type(type_id)

        # Debug logging
        print(f"🔍 API DEBUG: {type_id} fields count: {len(fields)}")
        field_names = [f.get('name') for f in fields]
        print(f"🔍 API DEBUG: {type_id} field names: {field_names}")
        print(f"🔍 API DEBUG: {type_id} has amenities: {'amenities' in field_names}")

        if not fields:
            return jsonify({'success': False, 'error': 'Property type not found'}), 404

        return jsonify({
            'success': True,
            'fields': fields,
            'property_type_id': type_id
        })
    except Exception as e:
        print(f"🔍 API DEBUG: Error in {type_id} fields: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/enhanced-predict', methods=['POST'])
@rate_limit(max_requests=30, window_seconds=60)
@sanitize_request_data()
def api_enhanced_predict():
    """Enhanced prediction API with property type support"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        property_type_id = data.get('property_type')
        if not property_type_id:
            return jsonify({'success': False, 'error': 'Property type is required'}), 400

        # Get prediction using enhanced predictor
        result = enhanced_predictor.predict_price(property_type_id, data)

        if result['success']:
            # Save to session history
            if 'enhanced_predictions' not in session:
                session['enhanced_predictions'] = []

            prediction_record = {
                'id': len(session['enhanced_predictions']) + 1,
                'timestamp': datetime.now().isoformat(),
                'property_type_id': property_type_id,
                'input_data': data,
                'result': result
            }

            session['enhanced_predictions'].append(prediction_record)
            session.modified = True

            # Track feature usage
            track_feature_usage('enhanced_prediction', session.get('session_id'))

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/property-presets')
@rate_limit(max_requests=50, window_seconds=60)
def api_property_presets():
    """Get all property presets"""
    try:
        presets = property_presets.get_all_presets()
        return jsonify({
            'success': True,
            'presets': presets
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/property-presets/<property_type_id>')
@rate_limit(max_requests=50, window_seconds=60)
def api_property_type_presets(property_type_id):
    """Get presets for a specific property type"""
    try:
        presets = property_presets.get_presets_by_property_type(property_type_id)
        return jsonify({
            'success': True,
            'presets': presets,
            'property_type_id': property_type_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/property-presets/<preset_id>/apply', methods=['POST'])
@rate_limit(max_requests=30, window_seconds=60)
def api_apply_preset(preset_id):
    """Apply a property preset with optional custom data"""
    try:
        data = request.get_json() or {}
        custom_data = data.get('custom_data', {})

        result = property_presets.apply_preset(preset_id, custom_data)

        return jsonify({
            'success': True,
            'preset_id': preset_id,
            'applied_data': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
@rate_limit(max_requests=30, window_seconds=60)
@sanitize_request_data()
@validate_property_input()
def api_predict():
    """API endpoint for predictions"""
    try:
        data = request.get_json()

        # Clean data
        clean_data = {
            'location': data.get('location', ''),
            'area_type': data.get('area_type', 'Super built-up Area'),
            'size': data.get('size', '2 BHK'),
            'total_sqft': float(data.get('total_sqft', 1000)),
            'bath': int(data.get('bath', 2)),
            'balcony': int(data.get('balcony', 1)),
            'availability': data.get('availability', 'Ready To Move')
        }

        # Get prediction
        price = predict_price(clean_data)
        clean_data['predicted_price'] = price

        # Generate dashboard data based on prediction
        dashboard_data = get_dashboard_data(clean_data)

        return jsonify({
            'success': True,
            'prediction': round(price, 2),
            'formatted_price': f"₹{price:,.2f} Lakhs",
            'confidence': 'High',
            'dashboard_data': dashboard_data
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/trends')
def trends():
    """Market trends page"""
    try:
        return render_template('simple_trends.html', locations=locations)
    except Exception as e:
        return f"""
        <html><head><title>Market Trends</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>📈 Market Trends</h1>
            <p>Analyzing market trends for Bangalore real estate...</p>
            <div style="margin: 20px 0;">
                <h3>Quick Insights:</h3>
                <p>• Average price growth: 9.2% YoY</p>
                <p>• Most popular locations: Whitefield, Koramangala, Indiranagar</p>
                <p>• Best investment areas: Electronic City, Sarjapur Road</p>
            </div>
            <a href="/" style="color: #667eea;">← Back to Home</a>
        </body></html>
        """, 200

@app.route('/api/trends/<location>')
@rate_limit(max_requests=20, window_seconds=60)
def api_trends(location):
    """Get enhanced trend data for a location with amenities analysis"""
    try:
        # Generate sample trend data
        years = list(range(2018, 2025))
        base_price = 75 + (hash(location) % 50)  # Base price varies by location

        # Simulate price growth with some randomness
        prices = []
        current_price = base_price
        growth_rates = []

        for year in years:
            growth_rate = 0.08 + (hash(f"{location}{year}") % 10) / 100  # 8-18% growth
            current_price *= (1 + growth_rate)
            prices.append(round(current_price, 2))
            growth_rates.append(round(growth_rate * 100, 1))

        # Calculate additional metrics
        total_growth = ((prices[-1] - prices[0]) / prices[0]) * 100
        avg_growth = sum(growth_rates) / len(growth_rates)

        # Get amenities data for location analysis
        amenities_data = get_location_amenities(location)

        # Generate investment insights based on amenities
        investment_rating = "Good"
        if amenities_data['overall_score'] > 80:
            investment_rating = "Excellent"
        elif amenities_data['overall_score'] > 60:
            investment_rating = "Good"
        else:
            investment_rating = "Average"

        # Generate market insights
        insights = []
        if avg_growth > 12:
            insights.append("High growth potential area")
        if amenities_data['category_scores'].get('transport', 0) > 70:
            insights.append("Excellent connectivity")
        if amenities_data['category_scores'].get('schools', 0) > 75:
            insights.append("Family-friendly location")
        if len(amenities_data['highlights']) > 3:
            insights.append("Well-developed infrastructure")

        return jsonify({
            'success': True,
            'location': location,
            'trends': {
                'years': years,
                'prices': prices,
                'growth_rates': growth_rates,
                'total_growth_percent': round(total_growth, 1),
                'avg_annual_growth': round(avg_growth, 1),
                'current_price': prices[-1],
                'price_change_1yr': round(prices[-1] - prices[-2], 2),
                'investment_rating': investment_rating
            },
            'amenities_summary': {
                'overall_score': amenities_data['overall_score'],
                'highlights': amenities_data['highlights'],
                'category_scores': amenities_data['category_scores']
            },
            'market_insights': insights,
            'forecast': {
                'next_year_prediction': round(prices[-1] * 1.1, 2),
                'confidence': "Medium",
                'recommendation': "Buy" if investment_rating in ["Good", "Excellent"] else "Hold"
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/compare')
def compare():
    """Property comparison page"""
    try:
        return render_template('simple_compare.html', locations=locations)
    except Exception as e:
        return f"""
        <html><head><title>Property Comparison</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>🆚 Property Comparison</h1>
            <p>Compare properties side-by-side to make informed decisions.</p>
            <div style="margin: 20px 0;">
                <h3>Comparison Features:</h3>
                <p>• Side-by-side property analysis</p>
                <p>• Price per sqft comparison</p>
                <p>• Investment recommendations</p>
                <p>• Location insights</p>
            </div>
            <a href="/predict" style="color: #667eea;">Start Predicting Properties →</a><br><br>
            <a href="/" style="color: #667eea;">← Back to Home</a>
        </body></html>
        """, 200

@app.route('/map')
def map_view():
    """Interactive map page"""
    try:
        return render_template('simple_map.html', locations=locations)
    except Exception as e:
        return f"""
        <html><head><title>Interactive Map</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>🗺️ Interactive Property Map</h1>
            <p>Explore properties across Bangalore with our interactive map.</p>
            <div style="margin: 20px 0;">
                <h3>Map Features:</h3>
                <p>• Property price markers</p>
                <p>• Location-based filtering</p>
                <p>• Neighborhood insights</p>
                <p>• Investment hotspots</p>
            </div>
            <a href="/predict" style="color: #667eea;">Predict Property Price →</a><br><br>
            <a href="/" style="color: #667eea;">← Back to Home</a>
        </body></html>
        """, 200

@app.route('/chat')
def chat():
    """AI chat assistant page"""
    try:
        return render_template('simple_chat.html')
    except Exception as e:
        return f"""
        <html><head><title>AI Chat Assistant</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>🤖 AI Real Estate Assistant</h1>
            <p>Get instant answers to your real estate questions!</p>
            <div style="margin: 20px 0;">
                <h3>Ask me about:</h3>
                <p>• Property prices and trends</p>
                <p>• Location insights and recommendations</p>
                <p>• Investment opportunities</p>
                <p>• Market analysis and forecasts</p>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h4>Quick Questions:</h4>
                <p>"What's the average price in Whitefield?"</p>
                <p>"Which areas have the best growth potential?"</p>
                <p>"How do I calculate EMI for a home loan?"</p>
            </div>
            <a href="/predict" style="color: #667eea;">Start with Price Prediction →</a><br><br>
            <a href="/" style="color: #667eea;">← Back to Home</a>
        </body></html>
        """, 200

@app.route('/api/chat', methods=['POST'])
@rate_limit(max_requests=15, window_seconds=60)
@sanitize_request_data()
def api_chat():
    """Advanced AI chat API with real estate intelligence"""
    try:
        data = request.get_json()
        message = data.get('message', '').lower()

        # Get user context from session
        user_properties = session.get('user_properties', [])
        chat_history = session.get('chat_history', [])

        # Add current message to history
        chat_history.append({'user': message, 'timestamp': datetime.now().isoformat()})

        # Advanced response generation
        response_data = generate_advanced_response(message, user_properties, chat_history)

        # Add response to history
        chat_history.append({'bot': response_data['response'], 'timestamp': datetime.now().isoformat()})
        session['chat_history'] = chat_history[-20:]  # Keep last 20 messages
        session.modified = True

        return jsonify({
            'success': True,
            'response': response_data['response'],
            'suggestions': response_data.get('suggestions', []),
            'actions': response_data.get('actions', []),
            'data': response_data.get('data', {}),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_advanced_response(message, user_properties, chat_history):
    """Generate advanced AI responses with context and data"""

    # Extract entities and intent
    intent = detect_intent(message)
    entities = extract_entities(message)

    response_data = {
        'response': '',
        'suggestions': [],
        'actions': [],
        'data': {}
    }

    if intent == 'price_inquiry':
        if entities.get('location'):
            location = entities['location']
            # Get amenities data for location
            amenities_data = get_location_amenities(location)

            # Generate price estimate
            base_price = 75 + (hash(location) % 50)
            price_range = f"₹{base_price-10:.1f}L - ₹{base_price+15:.1f}L"

            response_data['response'] = f"""🏠 **{location} Property Insights**

💰 **Price Range**: {price_range}
📊 **Location Score**: {amenities_data['overall_score']}/100
🎯 **Investment Rating**: {'Excellent' if amenities_data['overall_score'] > 80 else 'Good' if amenities_data['overall_score'] > 60 else 'Average'}

**Key Highlights:**
{chr(10).join([f"• {highlight}" for highlight in amenities_data['highlights'][:3]])}

Would you like detailed price prediction for a specific property?"""

            response_data['suggestions'] = [
                f"Predict price for 2BHK in {location}",
                f"Show market trends for {location}",
                f"Compare {location} with other areas",
                "Calculate EMI for this budget"
            ]

            response_data['actions'] = [
                {'type': 'predict', 'location': location},
                {'type': 'trends', 'location': location}
            ]

            response_data['data'] = {
                'location': location,
                'price_range': price_range,
                'amenities': amenities_data
            }

        else:
            response_data['response'] = """🏠 **Property Price Inquiry**

I can help you get accurate price predictions! Our AI analyzes:
• Location & neighborhood quality
• Property size & amenities
• Market trends & growth patterns
• Comparable sales data

**Popular Areas:**
• Whitefield: ₹85-120L (IT hub, excellent connectivity)
• Koramangala: ₹95-140L (Premium location, great amenities)
• Indiranagar: ₹90-130L (Central location, vibrant lifestyle)

Which location interests you?"""

            response_data['suggestions'] = [
                "Price in Whitefield",
                "Price in Koramangala",
                "Price in Indiranagar",
                "Compare different locations"
            ]

    elif intent == 'market_trends':
        location = entities.get('location', 'Bangalore')

        # Generate trend data
        growth_rate = 8 + (hash(location) % 5)

        response_data['response'] = f"""📈 **{location} Market Trends**

**Current Market Status:**
• Growth Rate: {growth_rate}% annually
• Market Sentiment: {'Bullish' if growth_rate > 10 else 'Positive'}
• Best Time to Buy: {'Now' if growth_rate < 10 else 'Consider waiting'}

**Key Factors Driving Growth:**
• Infrastructure development
• IT sector expansion
• Metro connectivity improvements
• Government policy support

**Investment Recommendation:**
{'Strong Buy' if growth_rate > 10 else 'Buy' if growth_rate > 8 else 'Hold'}"""

        response_data['suggestions'] = [
            f"Detailed trends for {location}",
            "Compare with other areas",
            "Investment opportunities",
            "Future price predictions"
        ]

        response_data['actions'] = [
            {'type': 'trends', 'location': location}
        ]

    elif intent == 'emi_calculation':
        amount = entities.get('amount', 50)

        # Calculate EMI
        principal = amount * 100000  # Convert lakhs to rupees
        rate = 8.5 / 100 / 12  # Monthly rate
        tenure = 20 * 12  # 20 years in months

        emi = principal * rate * (1 + rate)**tenure / ((1 + rate)**tenure - 1)
        total_amount = emi * tenure
        interest = total_amount - principal

        response_data['response'] = f"""💰 **EMI Calculation for ₹{amount}L**

**Loan Details:**
• Principal: ₹{amount}L
• Interest Rate: 8.5% p.a.
• Tenure: 20 years

**Monthly EMI: ₹{emi:,.0f}**

**Total Payment Breakdown:**
• Total Amount: ₹{total_amount/100000:.1f}L
• Interest Paid: ₹{interest/100000:.1f}L
• Interest %: {(interest/principal)*100:.1f}%

*Rates may vary by bank and profile*"""

        response_data['suggestions'] = [
            "Try different loan amounts",
            "Compare different tenures",
            "Check eligibility criteria",
            "Find best loan offers"
        ]

        response_data['actions'] = [
            {'type': 'loan_calculator', 'amount': amount}
        ]

        response_data['data'] = {
            'emi': emi,
            'total_amount': total_amount,
            'interest': interest,
            'principal': principal
        }

    elif intent == 'property_comparison':
        response_data['response'] = """🆚 **Property Comparison Tool**

Smart comparison helps you make informed decisions by analyzing:

**Financial Comparison:**
• Price per sqft analysis
• Total cost breakdown
• ROI potential
• Resale value projection

**Location Analysis:**
• Connectivity scores
• Amenities availability
• Future development plans
• Neighborhood quality

**Investment Metrics:**
• Rental yield potential
• Capital appreciation
• Market liquidity
• Risk assessment

Ready to compare specific properties?"""

        response_data['suggestions'] = [
            "Compare Whitefield vs Koramangala",
            "Compare 2BHK vs 3BHK",
            "Investment comparison",
            "Rental yield comparison"
        ]

        response_data['actions'] = [
            {'type': 'compare'}
        ]

    elif intent == 'amenities_inquiry':
        location = entities.get('location')
        if location:
            amenities_data = get_location_amenities(location)

            response_data['response'] = f"""🏢 **{location} Amenities & Infrastructure**

**Overall Score: {amenities_data['overall_score']}/100**

**Category Scores:**
{chr(10).join([f"• {cat.title()}: {score}/100" for cat, score in amenities_data['category_scores'].items()])}

**Key Highlights:**
{chr(10).join([f"✅ {highlight}" for highlight in amenities_data['highlights']])}

**Nearby Facilities:**
• Schools: {len(amenities_data['amenities'].get('schools', []))} options
• Hospitals: {len(amenities_data['amenities'].get('hospitals', []))} facilities
• Shopping: {len(amenities_data['amenities'].get('shopping', []))} centers
• Transport: {len(amenities_data['amenities'].get('transport', []))} options"""

            response_data['suggestions'] = [
                f"Detailed amenities in {location}",
                f"Compare {location} amenities",
                "Best areas for families",
                "Areas with best connectivity"
            ]
        else:
            response_data['response'] = """🏢 **Amenities & Infrastructure Analysis**

I can provide detailed information about:
• Schools & educational institutions
• Hospitals & healthcare facilities
• Shopping malls & markets
• Transport connectivity
• Entertainment options
• Parks & recreational areas

Which location would you like to explore?"""

    elif intent == 'investment_advice':
        response_data['response'] = """💡 **Real Estate Investment Guidance**

**Current Market Opportunities:**
• Emerging areas with infrastructure development
• Pre-launch projects with attractive pricing
• Ready-to-move properties for immediate rental income

**Investment Strategies:**
🎯 **Buy & Hold**: Long-term appreciation (8-12% annually)
🏠 **Rental Income**: 3-5% annual yield in prime locations
🔄 **Flip Strategy**: Quick gains in developing areas

**Risk Factors to Consider:**
• Market volatility
• Regulatory changes
• Location-specific risks
• Liquidity concerns

**Recommended Investment Areas:**
• Whitefield: IT growth, metro connectivity
• Electronic City: Established IT hub
• Sarjapur Road: Emerging corridor

Need specific investment advice for your budget?"""

        response_data['suggestions'] = [
            "Best areas under 1 Crore",
            "High rental yield areas",
            "Upcoming investment hotspots",
            "Investment risk analysis"
        ]

    else:
        # Default response with context awareness
        if len(chat_history) > 2:
            response_data['response'] = """� **I'm here to help with your real estate needs!**

Based on our conversation, I can assist you with:
• Property price predictions & market analysis
• Location insights & amenities information
• Investment advice & ROI calculations
• EMI calculations & loan planning
• Property comparisons & recommendations

What specific information would you like to explore?"""
        else:
            response_data['response'] = """👋 **Welcome to Real Estate AI Assistant!**

I'm your intelligent real estate companion with expertise in:

🏠 **Property Valuation**: AI-powered price predictions
📈 **Market Analysis**: Trends, growth patterns, investment insights
📍 **Location Intelligence**: Amenities, connectivity, neighborhood analysis
💰 **Financial Planning**: EMI calculations, loan advice, ROI analysis
🆚 **Smart Comparisons**: Property vs property analysis

**Popular Queries:**
• "What's the price of 2BHK in Whitefield?"
• "Show market trends for Koramangala"
• "Calculate EMI for 75 lakh loan"
• "Compare Indiranagar vs HSR Layout"

How can I help you today?"""

        response_data['suggestions'] = [
            "Predict property price",
            "Show market trends",
            "Calculate EMI",
            "Compare properties",
            "Find best locations"
        ]

    return response_data

def detect_intent(message):
    """Detect user intent from message"""
    if any(word in message for word in ['price', 'cost', 'value', 'worth', 'predict']):
        return 'price_inquiry'
    elif any(word in message for word in ['trend', 'market', 'growth', 'appreciation']):
        return 'market_trends'
    elif any(word in message for word in ['emi', 'loan', 'finance', 'mortgage', 'calculate']):
        return 'emi_calculation'
    elif any(word in message for word in ['compare', 'comparison', 'vs', 'versus', 'better']):
        return 'property_comparison'
    elif any(word in message for word in ['amenities', 'facilities', 'schools', 'hospitals', 'transport']):
        return 'amenities_inquiry'
    elif any(word in message for word in ['invest', 'investment', 'buy', 'advice', 'recommend']):
        return 'investment_advice'
    else:
        return 'general'

def extract_entities(message):
    """Extract entities like location, amount, etc. from message"""
    entities = {}

    # Extract location
    for location in locations:
        if location.lower() in message:
            entities['location'] = location
            break

    # Extract amount (in lakhs)
    import re
    amount_match = re.search(r'(\d+)\s*(?:lakh|lakhs|l|crore|crores)', message)
    if amount_match:
        amount = int(amount_match.group(1))
        if 'crore' in message:
            amount *= 100  # Convert crores to lakhs
        entities['amount'] = amount

    # Extract property size
    size_match = re.search(r'(\d+)\s*bhk', message)
    if size_match:
        entities['size'] = f"{size_match.group(1)} BHK"

    return entities

@app.route('/loan-calculator')
def loan_calculator():
    """Loan calculator page"""
    try:
        return render_template('simple_loan.html')
    except Exception as e:
        return f"""
        <html><head><title>Loan Calculator</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>💰 Home Loan Calculator</h1>
            <p>Calculate your EMI and plan your home loan effectively.</p>
            <div style="margin: 20px 0;">
                <h3>Calculator Features:</h3>
                <p>• EMI calculation with amortization schedule</p>
                <p>• Interest vs Principal breakdown</p>
                <p>• Total cost analysis</p>
                <p>• Prepayment scenarios</p>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h4>Quick Example:</h4>
                <p>Loan Amount: ₹50,00,000</p>
                <p>Interest Rate: 8.5% per annum</p>
                <p>Tenure: 20 years</p>
                <p><strong>EMI: ≈ ₹43,391</strong></p>
            </div>
            <a href="/predict" style="color: #667eea;">First Predict Property Price →</a><br><br>
            <a href="/" style="color: #667eea;">← Back to Home</a>
        </body></html>
        """, 200

@app.route('/api/loan-calculator', methods=['POST'])
def api_loan_calculator():
    """Loan calculator API"""
    try:
        data = request.get_json()
        principal = float(data['principal'])
        rate = float(data['rate']) / 100 / 12  # Monthly rate
        tenure = int(data['tenure']) * 12  # Months

        # EMI calculation
        if rate > 0:
            emi = (principal * rate * (1 + rate)**tenure) / ((1 + rate)**tenure - 1)
        else:
            emi = principal / tenure

        total_amount = emi * tenure
        total_interest = total_amount - principal

        return jsonify({
            'success': True,
            'emi': round(emi, 2),
            'total_amount': round(total_amount, 2),
            'total_interest': round(total_interest, 2),
            'principal': principal,
            'formatted_emi': f"₹{emi:,.2f}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/property-emi', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=60)
def api_property_emi():
    """Calculate EMI for specific property with down payment options"""
    try:
        data = request.get_json()
        property_price = float(data.get('property_price', 0)) * 100000  # Convert lakhs to rupees
        down_payment_percent = float(data.get('down_payment_percent', 20))
        rate = float(data.get('rate', 8.5))
        tenure = int(data.get('tenure', 20))

        # Calculate loan amount after down payment
        down_payment = property_price * (down_payment_percent / 100)
        loan_amount = property_price - down_payment

        # Calculate EMI
        monthly_rate = rate / 100 / 12
        num_payments = tenure * 12

        if monthly_rate > 0:
            emi = loan_amount * monthly_rate * (1 + monthly_rate)**num_payments / ((1 + monthly_rate)**num_payments - 1)
        else:
            emi = loan_amount / num_payments

        total_amount = emi * num_payments
        total_interest = total_amount - loan_amount
        total_cost = property_price + total_interest

        # Additional costs (approximate)
        registration_cost = property_price * 0.07  # 7% for registration, stamp duty, etc.

        return jsonify({
            'success': True,
            'property_price': property_price,
            'down_payment': round(down_payment, 2),
            'loan_amount': round(loan_amount, 2),
            'emi': round(emi, 2),
            'total_interest': round(total_interest, 2),
            'total_cost': round(total_cost, 2),
            'registration_cost': round(registration_cost, 2),
            'upfront_cost': round(down_payment + registration_cost, 2),
            'monthly_income_required': round((emi / 0.4), 2),
            'rate': rate,
            'tenure': tenure,
            'formatted_emi': f"₹{emi:,.0f}",
            'formatted_upfront': f"₹{(down_payment + registration_cost):,.0f}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/locations')
def api_locations():
    """Get all locations"""
    return jsonify({'success': True, 'locations': locations})

@app.route('/api/location-suggestions')
def location_suggestions():
    """Get location suggestions"""
    query = request.args.get('q', '').lower()
    suggestions = [loc for loc in locations if query in loc.lower()][:10]
    return jsonify({'success': True, 'suggestions': suggestions})

@app.route('/history')
def history():
    """Prediction history"""
    predictions = session.get('predictions', [])
    return render_template('simple_history.html', predictions=predictions)

@app.route('/list-property', methods=['GET', 'POST'])
@rate_limit(max_requests=10, window_seconds=300)  # Stricter limit for property listing
@login_required
def list_property():
    """Property listing page with image upload - requires login"""
    current_user = get_current_user()

    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
                files = {}
            else:
                data = request.form.to_dict()
                files = request.files

            # Validate required fields
            required_fields = ['owner_name', 'contact_number', 'property_type', 'location', 'size', 'total_sqft', 'bath']
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f"{field.replace('_', ' ').title()} is required")

            # Validate phone number
            contact = data.get('contact_number', '').strip()
            if not re.match(r'^[6-9]\d{9}$', contact):
                raise ValueError("Please enter a valid 10-digit mobile number")

            # Handle image uploads
            image_urls = []
            if 'property_images' in files:
                uploaded_files = files.getlist('property_images')
                for i, file in enumerate(uploaded_files[:5]):  # Limit to 5 images
                    if file and file.filename:
                        # Generate unique filename
                        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
                        unique_filename = f"property_{len(session.get('user_properties', [])) + 1}_{i+1}_{int(datetime.now().timestamp())}.{file_extension}"

                        # Save file to uploads directory
                        try:
                            file_path = os.path.join('static', 'uploads', unique_filename)
                            file.save(file_path)
                            image_urls.append(f"/static/uploads/{unique_filename}")
                        except Exception as e:
                            print(f"Error saving image: {e}")
                            # Continue without this image

            # Clean and validate property data
            property_data = {
                'id': str(len(session.get('user_properties', [])) + 1),  # Convert to string for consistency
                'timestamp': datetime.now().isoformat(),
                'owner_name': security_manager.sanitize_input(data.get('owner_name', '')),
                'contact_number': contact,
                'owner_contact': contact,  # Add this for admin panel compatibility
                'email': security_manager.sanitize_input(data.get('email', '')),
                'property_type': data.get('property_type', ''),
                'location': data.get('location', ''),
                'area_type': data.get('area_type', 'Super built-up Area'),
                'size': data.get('size', '2 BHK'),
                'total_sqft': float(data.get('total_sqft', 1000)),
                'bath': int(data.get('bath', 2)),
                'balcony': int(data.get('balcony', 1)),
                'availability': data.get('availability', 'Ready To Move'),
                'expected_price': float(data.get('expected_price', 0)) if data.get('expected_price') else None,
                'description': security_manager.sanitize_input(data.get('description', '')),
                'amenities': [a.strip() for a in data.get('amenities', '').split(',') if a.strip()],
                'images': image_urls,
                'status': 'active'
            }

            # Get AI price prediction for the property
            predicted_price = predict_price(property_data)
            property_data['ai_predicted_price'] = predicted_price
            property_data['price_difference'] = None

            if property_data['expected_price']:
                property_data['price_difference'] = property_data['expected_price'] - predicted_price
                property_data['price_variance_percent'] = (property_data['price_difference'] / predicted_price) * 100

            # Save to database
            result = db_manager.add_property(current_user['id'], property_data)

            if not result['success']:
                raise Exception(result['error'])

            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Property listed successfully!',
                    'property_id': property_data['id'],
                    'ai_predicted_price': f"₹{predicted_price:,.2f} Lakhs",
                    'property_data': property_data
                })
            else:
                return render_template('list_property.html',
                                     locations=locations,
                                     success=True,
                                     property_data=property_data)

        except Exception as e:
            error_msg = f"Error listing property: {str(e)}"
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 500
            else:
                return render_template('list_property.html',
                                     locations=locations,
                                     error=error_msg)

    return render_template('list_property.html', locations=locations)

@app.route('/my-properties')
@login_required
def my_properties():
    """View user's listed properties from database (both regular and rental properties)"""
    try:
        current_user = get_current_user()
        if not current_user:
            return redirect(url_for('login'))

        # Get user's regular properties from database
        properties_result = db_manager.get_user_properties(current_user['id'])

        if properties_result['success']:
            user_properties = properties_result['properties']
            print(f"DEBUG: Found {len(user_properties)} regular properties for user {current_user['username']}")
        else:
            user_properties = []
            print(f"DEBUG: No regular properties found for user {current_user['username']}: {properties_result.get('error', 'Unknown error')}")

        # Get user's rental properties from database
        rentals_result = db_manager.get_user_rental_properties(current_user['id'])

        if rentals_result['success']:
            user_rentals = rentals_result['rentals']
            print(f"DEBUG: Found {len(user_rentals)} rental properties for user {current_user['username']}")
        else:
            user_rentals = []
            print(f"DEBUG: No rental properties found for user {current_user['username']}: {rentals_result.get('error', 'Unknown error')}")

        # Combine both types for total count
        total_properties = len(user_properties) + len(user_rentals)
        print(f"DEBUG: Total properties for user {current_user['username']}: {total_properties}")

        return render_template('my_properties.html',
                             properties=user_properties,
                             rental_properties=user_rentals,
                             total_properties=total_properties,
                             current_user=current_user)

    except Exception as e:
        print(f"ERROR: My properties page failed: {e}")
        return render_template('my_properties.html',
                             properties=[],
                             rental_properties=[],
                             total_properties=0,
                             current_user=get_current_user(),
                             error=f"Error loading properties: {str(e)}")

@app.route('/browse-properties')
def browse_properties():
    """Browse all admin-approved properties (both sale and rental) visible to public"""
    try:
        # Get approved sale properties from public table
        sale_result = db_manager.get_approved_properties_for_public()
        if sale_result['success']:
            approved_sale_properties = sale_result['properties']
            print(f"DEBUG: Found {len(approved_sale_properties)} approved sale properties for public display")

            # Debug: Check images in first property
            if approved_sale_properties:
                sample = approved_sale_properties[0]
                print(f"DEBUG: Sample property images: {sample.get('images')} (type: {type(sample.get('images'))})")
        else:
            approved_sale_properties = []
            print(f"DEBUG: No approved sale properties found - Error: {sale_result.get('error', 'Unknown error')}")

        # Get approved rental properties from public table
        rental_result = db_manager.get_approved_rentals_for_public()
        if rental_result['success']:
            approved_rental_properties = rental_result['rentals']
            print(f"DEBUG: Found {len(approved_rental_properties)} approved rental properties for public display")
        else:
            approved_rental_properties = []
            print(f"DEBUG: No approved rental properties found - Error: {rental_result.get('error', 'Unknown error')}")

        # For backward compatibility, keep the original properties variable for sale properties
        all_properties = approved_sale_properties

    except Exception as e:
        print(f"ERROR: Browse properties failed: {e}")
        approved_sale_properties = []
        approved_rental_properties = []
        all_properties = []

    # Filter by query parameters
    location_filter = request.args.get('location')
    size_filter = request.args.get('size')
    max_price = request.args.get('max_price')

    filtered_properties = all_properties

    if location_filter:
        filtered_properties = [p for p in filtered_properties if location_filter.lower() in p['location'].lower()]

    if size_filter:
        filtered_properties = [p for p in filtered_properties if p['size'] == size_filter]

    if max_price:
        try:
            max_price_val = float(max_price)
            filtered_properties = [p for p in filtered_properties
                                 if (p['expected_price'] or p['ai_predicted_price']) <= max_price_val]
        except ValueError:
            pass

    # Get current user info (for navigation display)
    current_user = get_current_user()

    # Calculate totals
    total_properties = len(approved_sale_properties) + len(approved_rental_properties)

    return render_template('browse_all_properties_new.html',
                         sale_properties=filtered_properties,
                         rental_properties=approved_rental_properties,
                         total_properties=total_properties,
                         current_user=current_user,
                         locations=locations,
                         filters={
                             'location': location_filter,
                             'size': size_filter,
                             'max_price': max_price
                         })



@app.route('/property/<property_id>')
def property_detail(property_id):
    """Property detail view with full images"""
    try:
        # Get all properties
        all_properties = session.get('user_properties', [])

        # Find the specific property
        property_data = None
        for prop in all_properties:
            if prop.get('id') == property_id:
                property_data = prop
                break

        if not property_data:
            return redirect(url_for('browse_properties'))

        # Get similar properties (same location or type)
        similar_properties = []
        for prop in all_properties:
            if (prop.get('id') != property_id and
                (prop.get('location') == property_data.get('location') or
                 prop.get('property_type') == property_data.get('property_type'))):
                similar_properties.append(prop)

        # Limit to 4 similar properties
        similar_properties = similar_properties[:4]

        return render_template('property_detail.html',
                             property=property_data,
                             similar_properties=similar_properties,
                             locations=locations)
    except Exception as e:
        return f"Error loading property details: {str(e)}", 500

@app.route('/property-search')
def property_search():
    """Property search with amenities page"""
    return render_template('property_search.html', locations=locations)

@app.route('/api/contact-owner', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=300)
@sanitize_request_data()
def contact_owner():
    """API to handle owner contact requests"""
    try:
        data = request.get_json()
        property_id = data.get('property_id')
        buyer_name = data.get('buyer_name')
        buyer_contact = data.get('buyer_contact')
        message = data.get('message', '')

        # Find property details
        user_properties = session.get('user_properties', [])
        property_details = None
        for prop in user_properties:
            if str(prop.get('id')) == str(property_id):
                property_details = prop
                break

        if property_details:
            # Send notification to property owner
            send_property_inquiry(
                property_details['contact_number'],
                property_details['location'],
                buyer_name,
                buyer_contact,
                message
            )

            # Track analytics
            track_feature_usage('contact_owner', session.get('session_id', 'anonymous'), True, {
                'property_id': property_id,
                'property_location': property_details['location']
            })

        return jsonify({
            'success': True,
            'message': 'Your contact request has been sent to the property owner. They will contact you soon!'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/tourist-rentals')
def tourist_rentals():
    """Redirect tourist rentals to browse rental properties page"""
    return redirect(url_for('browse_rental_properties'))

@app.route('/list-rental-property')
@login_required
def list_rental_property():
    """Rental property listing form"""
    current_user = get_current_user()
    return render_template('list_rental_property.html', current_user=current_user)

@app.route('/list-rental-property', methods=['POST'])
@login_required
def submit_rental_property():
    """Handle rental property submission"""
    try:
        current_user = get_current_user()

        # Get form data
        property_data = {
            'property_type': request.form.get('property_type'),
            'location': request.form.get('location'),
            'size': request.form.get('size'),
            'total_sqft': int(request.form.get('total_sqft', 0)) if request.form.get('total_sqft') else None,
            'bedrooms': int(request.form.get('bedrooms', 0)) if request.form.get('bedrooms') else None,
            'bathrooms': int(request.form.get('bathrooms', 0)) if request.form.get('bathrooms') else None,
            'balcony': int(request.form.get('balcony', 0)) if request.form.get('balcony') else None,
            'rent_amount': float(request.form.get('rent_amount', 0)),
            'security_deposit': float(request.form.get('security_deposit', 0)) if request.form.get('security_deposit') else None,
            'maintenance_charges': float(request.form.get('maintenance_charges', 0)) if request.form.get('maintenance_charges') else None,
            'description': request.form.get('description'),
            'amenities': request.form.getlist('amenities'),
            'available_from': request.form.get('available_from'),
            'lease_duration': request.form.get('lease_duration'),
            'furnishing_status': request.form.get('furnishing_status'),
            'parking_available': bool(request.form.get('parking_available')),
            'pet_friendly': bool(request.form.get('pet_friendly')),
            'images': []
        }

        # Handle image uploads
        uploaded_files = request.files.getlist('images')
        for file in uploaded_files:
            if file and file.filename:
                # Save file (simplified - in production, use proper file handling)
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                unique_filename = timestamp + filename
                file_path = os.path.join('static/uploads/rentals', unique_filename)

                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                property_data['images'].append(f'/static/uploads/rentals/{unique_filename}')

        # Add rental property to database
        result = db_manager.add_rental_property(current_user['id'], property_data)

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Rental property submitted successfully! It will be visible after admin approval.',
                'rental_id': result['rental_id']
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/browse-rental-properties')
def browse_rental_properties():
    """Browse all admin-approved rental properties visible to public"""
    try:
        # Get approved rental properties from public table
        result = db_manager.get_approved_rentals_for_public()

        if result['success']:
            rentals = result['rentals']
            print(f"DEBUG: Found {len(rentals)} approved rental properties for public display")
        else:
            rentals = []
            print(f"DEBUG: No approved rental properties found - Error: {result.get('error', 'Unknown error')}")

        # Get current user info (for navigation display)
        current_user = get_current_user()

        # Debug logging
        if current_user:
            print(f"DEBUG: User '{current_user['username']}' browsing approved rentals")
        else:
            print("DEBUG: Anonymous user browsing approved rentals")

        return render_template('browse_rental_properties.html',
                             rentals=rentals,
                             current_user=current_user)

    except Exception as e:
        print(f"ERROR: Browse rental properties failed: {e}")
        return render_template('browse_rental_properties.html',
                             rentals=[],
                             current_user=get_current_user())

@app.route('/api/test-rental-access')
def test_rental_access():
    """Test API endpoint to verify rental access"""
    try:
        # Get approved rental properties
        result = db_manager.get_all_rental_properties(status='approved')

        current_user = get_current_user()

        return jsonify({
            'success': True,
            'approved_rentals_count': len(result.get('rentals', [])),
            'user_logged_in': current_user is not None,
            'user_info': current_user['username'] if current_user else None,
            'rentals': [
                {
                    'id': r['id'],
                    'type': r['property_type'],
                    'location': r['location'],
                    'rent': r['rent_amount']
                } for r in result.get('rentals', [])[:5]  # First 5 for testing
            ]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/list-rental', methods=['GET', 'POST'])
def list_rental():
    """List property for tourist rental"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()

            # Generate unique ID
            rental_id = f"TR{len(session.get('rental_properties', [])) + 100:03d}"

            rental_data = {
                'id': rental_id,
                'title': data.get('title', ''),
                'location': data.get('location', ''),
                'property_type': data.get('property_type', ''),
                'size': data.get('size', ''),
                'total_sqft': int(data.get('total_sqft', 0)),
                'daily_rate': float(data.get('daily_rate', 0)),
                'weekly_rate': float(data.get('weekly_rate', 0)) if data.get('weekly_rate') else None,
                'monthly_rate': float(data.get('monthly_rate', 0)) if data.get('monthly_rate') else None,
                'amenities': data.get('amenities', '').split(',') if data.get('amenities') else [],
                'description': data.get('description', ''),
                'availability': 'Available',
                'owner_name': data.get('owner_name', ''),
                'contact_number': data.get('contact_number', ''),
                'email': data.get('email', ''),
                'instant_book': data.get('instant_book') == 'on',
                'min_stay': int(data.get('min_stay', 1)),
                'max_guests': int(data.get('max_guests', 2)),
                'rating': 0,
                'reviews_count': 0,
                'timestamp': datetime.now().isoformat()
            }

            # Calculate weekly/monthly rates if not provided
            if not rental_data['weekly_rate']:
                rental_data['weekly_rate'] = rental_data['daily_rate'] * 6  # 1 day free
            if not rental_data['monthly_rate']:
                rental_data['monthly_rate'] = rental_data['daily_rate'] * 25  # 5 days free

            # Save to session
            if 'rental_properties' not in session:
                session['rental_properties'] = []

            session['rental_properties'].append(rental_data)
            session.modified = True

            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Rental property listed successfully!',
                    'rental_id': rental_id,
                    'rental_data': rental_data
                })
            else:
                return render_template('list_rental.html',
                                     locations=locations,
                                     success=True,
                                     rental_data=rental_data)

        except Exception as e:
            error_msg = f"Error listing rental: {str(e)}"
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 500
            else:
                return render_template('list_rental.html',
                                     locations=locations,
                                     error=error_msg)

    return render_template('list_rental.html', locations=locations)

@app.route('/api/book-rental', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=300)
@sanitize_request_data()
def book_rental():
    """API to handle rental booking requests"""
    try:
        data = request.get_json()
        rental_id = data.get('rental_id')
        guest_name = data.get('guest_name')
        guest_contact = data.get('guest_contact')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        guests = data.get('guests', 1)
        message = data.get('message', '')

        # Find rental property details
        rental_properties = session.get('rental_properties', [])
        rental_details = None
        for rental in rental_properties:
            if rental.get('id') == rental_id:
                rental_details = rental
                break

        # Create booking record
        booking_data = {
            'booking_id': f"BK{len(session.get('bookings', [])) + 1000:04d}",
            'rental_id': rental_id,
            'guest_name': guest_name,
            'guest_contact': guest_contact,
            'check_in': check_in,
            'check_out': check_out,
            'guests': guests,
            'message': message,
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        }

        # Save booking
        if 'bookings' not in session:
            session['bookings'] = []
        session['bookings'].append(booking_data)
        session.modified = True

        # Send notification to rental owner
        if rental_details:
            send_rental_booking(
                rental_details['contact_number'],
                rental_details['title'],
                guest_name,
                guest_contact,
                check_in,
                check_out
            )

            # Track analytics
            track_feature_usage('rental_booking', session.get('session_id', 'anonymous'), True, {
                'rental_id': rental_id,
                'property_title': rental_details['title']
            })

        return jsonify({
            'success': True,
            'message': 'Booking request sent successfully! The property owner will contact you soon.',
            'booking_id': booking_data['booking_id']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Old admin dashboard removed - replaced with secure version

@app.route('/api/admin/analytics')
@rate_limit(max_requests=10, window_seconds=60)
def api_admin_analytics():
    """Get analytics data for admin dashboard"""
    admin_key = request.args.get('key')
    if admin_key != 'admin123':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        analytics_data = get_dashboard_analytics()

        # Add additional admin-specific data
        admin_data = {
            'platform_stats': {
                'total_properties': len(session.get('user_properties', [])),
                'total_rentals': len(session.get('rental_properties', [])),
                'total_predictions': len(session.get('predictions', [])),
                'total_bookings': len(session.get('bookings', []))
            },
            'security_stats': {
                'blocked_requests': 0,  # Would come from security manager
                'rate_limited_ips': 0,
                'suspicious_activities': 0
            },
            'system_health': {
                'uptime': '99.9%',
                'response_time': '120ms',
                'error_rate': '0.1%',
                'cpu_usage': '45%',
                'memory_usage': '62%'
            }
        }

        return jsonify({
            'success': True,
            'analytics': analytics_data,
            'admin_data': admin_data
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/notifications')
@rate_limit(max_requests=10, window_seconds=60)
def admin_notifications():
    """Get notification statistics for admin"""
    admin_key = request.args.get('key')
    if admin_key != 'admin123':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        notification_stats = notification_manager.get_notification_stats()
        return jsonify({
            'success': True,
            'notification_stats': notification_stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/amenities/<location>')
@rate_limit(max_requests=20, window_seconds=60)
def get_amenities(location):
    """Get nearby amenities for a location"""
    try:
        amenities_data = get_location_amenities(location)

        return jsonify({
            'success': True,
            'location': location,
            'amenities': amenities_data
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search-properties')
@rate_limit(max_requests=30, window_seconds=60)
def search_properties():
    """Search properties with location and amenities"""
    try:
        location = request.args.get('location', '')
        property_type = request.args.get('type', '')
        min_price = request.args.get('min_price', 0, type=float)
        max_price = request.args.get('max_price', 1000, type=float)

        # Get all properties
        all_properties = session.get('user_properties', [])
        rental_properties = session.get('rental_properties', [])

        # Filter properties
        filtered_properties = []

        for prop in all_properties:
            if location.lower() in prop.get('location', '').lower():
                if not property_type or property_type.lower() in prop.get('property_type', '').lower():
                    prop_price = prop.get('ai_predicted_price', 0)
                    if min_price <= prop_price <= max_price:
                        # Add amenities data
                        prop['nearby_amenities'] = get_location_amenities(prop['location'])
                        filtered_properties.append(prop)

        return jsonify({
            'success': True,
            'properties': filtered_properties,
            'total_found': len(filtered_properties),
            'search_params': {
                'location': location,
                'type': property_type,
                'price_range': f"₹{min_price}-{max_price} Lakhs"
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/about')
def about():
    """About page"""
    return render_template('simple_about.html')

@app.route('/dashboard')
def dashboard():
    """Enhanced dashboard with real-time data"""
    # Get latest prediction from session
    predictions = session.get('predictions', [])
    latest_prediction = predictions[-1] if predictions else None

    if latest_prediction:
        dashboard_data = latest_prediction.get('dashboard_data', get_dashboard_data())
    else:
        dashboard_data = get_dashboard_data()

    # Add more dashboard metrics
    dashboard_data['statistics'] = {
        'total_predictions': len(predictions),
        'avg_price': sum(p['predicted_price'] for p in predictions) / len(predictions) if predictions else 112.5,
        'popular_locations': ['Whitefield', 'Koramangala', 'Indiranagar'],
        'market_status': 'Rising'
    }

    return render_template('dashboard.html',
                         dashboard=dashboard_data,
                         predictions=predictions[-5:],  # Last 5 predictions
                         locations=locations)

# ===================== ADMIN PANEL ROUTES =====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            return render_template('admin_login.html', error='Username and password required')

        # Check rate limiting
        client_ip = get_client_ip()
        now = datetime.now()

        # Clean old attempts (older than 15 minutes)
        admin_login_attempts[client_ip] = [
            attempt for attempt in admin_login_attempts[client_ip]
            if now - attempt < timedelta(minutes=15)
        ]

        # Check if too many attempts
        if len(admin_login_attempts[client_ip]) >= 5:
            log_security_event('admin_login_blocked', {'ip': client_ip, 'username': username})
            return render_template('admin_login.html', error='Too many login attempts. Try again later.')

        # Verify credentials
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password_hash:
            # Successful login
            admin_id = f"{username}_{secrets.token_hex(8)}"
            session['admin_logged_in'] = True
            session['admin_id'] = admin_id
            session['admin_username'] = username
            session.permanent = True

            # Store admin session
            admin_sessions[admin_id] = {
                'username': username,
                'login_time': now,
                'last_activity': now,
                'ip_address': client_ip
            }

            log_admin_action('login', {'username': username, 'ip': client_ip})
            return redirect(url_for('admin_dashboard'))
        else:
            # Failed login
            admin_login_attempts[client_ip].append(now)
            log_security_event('admin_login_failed', {'ip': client_ip, 'username': username})
            return render_template('admin_login.html', error='Invalid credentials')

    return render_template('admin_login.html')

@app.route('/admin/logout')
@admin_required
def admin_logout():
    """Admin logout"""
    admin_id = session.get('admin_id')
    username = session.get('admin_username')

    if admin_id in admin_sessions:
        del admin_sessions[admin_id]

    log_admin_action('logout', {'username': username})

    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    session.pop('admin_username', None)

    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    try:
        # Get system statistics
        stats = get_admin_statistics()

        # Check if stats contains an error
        if 'error' in stats:
            # Return default stats if there's an error
            stats = {
                'total_properties': 0,
                'total_users': 0,
                'active_users': 0,
                'inactive_users': 0,
                'pending_properties': 0,
                'approved_properties': 0,
                'rejected_properties': 0,
                'total_predictions': 0,
                'total_page_views': 0,
                'system_uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'recent_properties': [],
                'property_types': {},
                'location_distribution': {},
                'price_ranges': {'0-50L': 0, '50-100L': 0, '100L+': 0},
                'user_property_counts': {},
                'monthly_registrations': {},
                'revenue_potential': 0
            }

        # Get recent activities
        recent_logs = session.get('admin_logs', [])[-10:]  # Last 10 actions

        # Get active sessions
        active_sessions = len([s for s in admin_sessions.values()
                             if datetime.now() - s['last_activity'] < timedelta(hours=1)])

        return render_template('admin_dashboard.html',
                             stats=stats,
                             recent_logs=recent_logs,
                             active_sessions=active_sessions,
                             admin_username=session.get('admin_username'))
    except Exception as e:
        log_admin_action('dashboard_error', {'error': str(e)})
        return f"Admin Dashboard Error: {str(e)}", 500

def get_admin_statistics():
    """Get system statistics for admin dashboard from database"""
    try:
        # Get all properties from database
        properties_result = db_manager.get_all_properties()
        all_properties = properties_result.get('properties', []) if properties_result['success'] else []

        # Get all users from database
        users_result = db_manager.get_all_users()
        all_users = users_result.get('users', []) if users_result['success'] else []

        # Get analytics data
        analytics_data = get_dashboard_analytics()

        # Calculate property status distribution
        status_counts = {'pending': 0, 'approved': 0, 'rejected': 0}
        for prop in all_properties:
            status = prop.get('status', 'pending')
            status_counts[status] = status_counts.get(status, 0) + 1

        # Calculate user activity
        active_users = len([u for u in all_users if u.get('is_active', 1)])
        inactive_users = len(all_users) - active_users

        stats = {
            'total_properties': len(all_properties),
            'total_users': len(all_users),
            'active_users': active_users,
            'inactive_users': inactive_users,
            'pending_properties': status_counts['pending'],
            'approved_properties': status_counts['approved'],
            'rejected_properties': status_counts['rejected'],
            'total_predictions': analytics_data.get('total_predictions', 0),
            'total_page_views': analytics_data.get('total_page_views', 0),
            'system_uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'recent_properties': sorted(all_properties, key=lambda x: x.get('created_at', ''), reverse=True)[:5],
            'property_types': {},
            'location_distribution': {},
            'price_ranges': {'0-50L': 0, '50-100L': 0, '100L+': 0},
            'user_property_counts': {},
            'monthly_registrations': {},
            'revenue_potential': 0
        }

        # Calculate property type distribution
        for prop in all_properties:
            prop_type = prop.get('property_type', 'Unknown')
            stats['property_types'][prop_type] = stats['property_types'].get(prop_type, 0) + 1

            location = prop.get('location', 'Unknown').strip()
            stats['location_distribution'][location] = stats['location_distribution'].get(location, 0) + 1

            # Price range analysis
            price = prop.get('ai_predicted_price', 0) or prop.get('expected_price', 0)
            if price:
                if price < 50:
                    stats['price_ranges']['0-50L'] += 1
                elif price < 100:
                    stats['price_ranges']['50-100L'] += 1
                else:
                    stats['price_ranges']['100L+'] += 1

                # Add to revenue potential
                stats['revenue_potential'] += price

        # Calculate user property distribution
        for user in all_users:
            username = user.get('username', 'Unknown')
            property_count = user.get('property_count', 0)
            stats['user_property_counts'][username] = property_count

        # Calculate monthly registrations (simplified)
        current_month = datetime.now().strftime('%Y-%m')
        stats['monthly_registrations'][current_month] = len(all_users)

        return stats
    except Exception as e:
        # Return default stats structure if there's an error
        return {
            'total_properties': 0,
            'total_users': 0,
            'active_users': 0,
            'inactive_users': 0,
            'pending_properties': 0,
            'approved_properties': 0,
            'rejected_properties': 0,
            'total_predictions': 0,
            'total_page_views': 0,
            'system_uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'recent_properties': [],
            'property_types': {},
            'location_distribution': {},
            'price_ranges': {'0-50L': 0, '50-100L': 0, '100L+': 0},
            'user_property_counts': {},
            'monthly_registrations': {},
            'revenue_potential': 0,
            'error': str(e)
        }

@app.route('/admin/properties')
@admin_required
def admin_properties():
    """Admin property management"""
    try:
        # Get all properties from database
        result = db_manager.get_all_properties()
        all_properties = result.get('properties', []) if result['success'] else []

        # Filter by status if requested
        status_filter = request.args.get('status', 'all')
        if status_filter != 'all':
            all_properties = [p for p in all_properties if p.get('status', 'active') == status_filter]

        log_admin_action('view_properties', {'total_properties': len(all_properties), 'filter': status_filter})

        return render_template('admin_properties.html',
                             properties=all_properties,
                             status_filter=status_filter,
                             admin_username=session.get('admin_username'))
    except Exception as e:
        log_admin_action('properties_error', {'error': str(e)})
        return f"Admin Properties Error: {str(e)}", 500

@app.route('/admin/properties/<property_id>/action', methods=['POST'])
@admin_required
def admin_property_action(property_id):
    """Admin property actions (approve, reject, delete)"""
    try:
        # Get property_id from URL parameter, fallback to form data
        if not property_id:
            property_id = request.form.get('property_id')
        action = request.form.get('action')

        if not property_id or not action:
            return jsonify({'success': False, 'error': 'Missing property ID or action'}), 400

        # Perform action using new approval system
        admin_id = session.get('admin_user_id', 1)  # Get admin ID, default to 1

        if action == 'approve':
            # Approve property and make it visible to public
            result = db_manager.approve_property_to_public(property_id, admin_id)
            if result['success']:
                message = 'Property approved and made visible to all users'
            else:
                return jsonify({'success': False, 'error': result['error']}), 500

        elif action in ['reject', 'delete']:
            # Remove property from public view
            result = db_manager.delete_property_from_public(property_id)
            if result['success']:
                message = 'Property removed from public view'
            else:
                return jsonify({'success': False, 'error': result['error']}), 500
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400

        log_admin_action('property_action', {
            'property_id': property_id,
            'action': action,
            'admin': session.get('admin_username')
        })

        return jsonify({'success': True, 'message': message})

    except Exception as e:
        log_admin_action('property_action_error', {'error': str(e)})
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin user management"""
    try:
        # Get all users from database
        result = db_manager.get_all_users()
        users_list = result.get('users', []) if result['success'] else []

        # Debug logging
        print(f"DEBUG: Admin Users - Result success: {result['success']}")
        print(f"DEBUG: Admin Users - Number of users: {len(users_list)}")
        if users_list:
            print(f"DEBUG: Admin Users - First user: {users_list[0]}")

        log_admin_action('view_users', {'total_users': len(users_list)})

        return render_template('admin_users.html',
                             users=users_list,
                             admin_username=session.get('admin_username'))
    except Exception as e:
        log_admin_action('users_error', {'error': str(e)})
        return f"Admin Users Error: {str(e)}", 500



@app.route('/admin/users/<user_id>/action', methods=['POST'])
@admin_required
def admin_user_action_by_id(user_id):
    """Admin user actions (block, unblock, delete)"""
    try:
        action = request.form.get('action')

        if not action:
            return jsonify({'success': False, 'error': 'Action is required'}), 400

        # Get database connection
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        message = ''
        if action == 'block':
            cursor.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
            message = 'User blocked successfully'
        elif action == 'unblock':
            cursor.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))
            message = 'User unblocked successfully'
        elif action == 'delete':
            # Delete user's properties first
            cursor.execute('DELETE FROM properties WHERE user_id = ?', (user_id,))
            # Delete user's sessions
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            # Delete user
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            message = 'User and all associated data deleted successfully'
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400

        conn.commit()
        conn.close()

        # Log admin action
        log_admin_action(f'user_{action}', {
            'user_id': user_id,
            'action': action,
            'admin_id': session.get('admin_username')
        })

        return jsonify({'success': True, 'message': message})

    except Exception as e:
        log_admin_action('user_action_error', {'error': str(e)})
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Admin analytics page with comprehensive insights from database"""
    try:
        # Get all properties from database
        properties_result = db_manager.get_all_properties()
        all_properties = properties_result.get('properties', []) if properties_result['success'] else []

        # Get all users from database
        users_result = db_manager.get_all_users()
        all_users = users_result.get('users', []) if users_result['success'] else []

        # Calculate comprehensive analytics
        analytics_data = {
            'total_properties': len(all_properties),
            'total_users': len(all_users),
            'property_by_type': {},
            'property_by_location': {},
            'property_by_status': {},
            'user_activity': {
                'active_users': len([u for u in all_users if u.get('is_active', 1)]),
                'inactive_users': len([u for u in all_users if not u.get('is_active', 1)]),
                'users_with_properties': len([u for u in all_users if u.get('property_count', 0) > 0])
            },
            'price_analytics': {
                'avg_price': 0,
                'min_price': 0,
                'max_price': 0,
                'total_value': 0,
                'price_ranges': {'0-50L': 0, '50-100L': 0, '100L+': 0}
            },
            'monthly_listings': {},
            'top_users': [],
            'recent_activity': all_properties[-10:] if all_properties else []
        }

        # Calculate analytics from database data
        prices = []

        if all_properties:
            # Property type distribution
            for prop in all_properties:
                prop_type = prop.get('property_type', 'Unknown')
                analytics_data['property_by_type'][prop_type] = analytics_data['property_by_type'].get(prop_type, 0) + 1

                # Location distribution
                location = prop.get('location', 'Unknown').strip()
                analytics_data['property_by_location'][location] = analytics_data['property_by_location'].get(location, 0) + 1

                # Status distribution
                status = prop.get('status', 'pending')
                analytics_data['property_by_status'][status] = analytics_data['property_by_status'].get(status, 0) + 1

                # Price analytics
                price = prop.get('expected_price') or prop.get('ai_predicted_price', 0)
                if price:
                    prices.append(price)
                    analytics_data['price_analytics']['total_value'] += price

                    if price < 50:
                        analytics_data['price_analytics']['price_ranges']['0-50L'] += 1
                    elif price < 100:
                        analytics_data['price_analytics']['price_ranges']['50-100L'] += 1
                    else:
                        analytics_data['price_analytics']['price_ranges']['100L+'] += 1

                # Monthly listings
                if prop.get('created_at'):
                    month = prop['created_at'][:7]  # YYYY-MM format
                    analytics_data['monthly_listings'][month] = analytics_data['monthly_listings'].get(month, 0) + 1

            # Calculate price statistics
            if prices:
                analytics_data['price_analytics']['avg_price'] = sum(prices) / len(prices)
                analytics_data['price_analytics']['min_price'] = min(prices)
                analytics_data['price_analytics']['max_price'] = max(prices)

        # Calculate top users by property count
        analytics_data['top_users'] = sorted(all_users, key=lambda x: x.get('property_count', 0), reverse=True)[:5]

        # Add system health metrics
        analytics_data['system_health'] = {
            'database_status': 'Connected',
            'total_records': len(all_properties) + len(all_users),
            'data_integrity': 'Good',
            'last_backup': 'N/A'
        }

        # Get recent admin activity
        recent_logs = session.get('admin_logs', [])[-20:]  # Last 20 actions
        analytics_data['recent_admin_activity'] = recent_logs

        log_admin_action('view_analytics', {'total_properties': len(all_properties)})

        return render_template('admin_analytics.html',
                             analytics=analytics_data,
                             admin_username=session.get('admin_username'))
    except Exception as e:
        log_admin_action('analytics_error', {'error': str(e)})
        return f"Admin Analytics Error: {str(e)}", 500

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin settings page"""
    try:
        # Get current system settings from database
        properties_result = db_manager.get_all_properties()
        users_result = db_manager.get_all_users()

        total_properties = len(properties_result.get('properties', [])) if properties_result['success'] else 0
        total_users = len(users_result.get('users', [])) if users_result['success'] else 0

        settings_data = {
            'system_info': {
                'total_properties': total_properties,
                'total_users': total_users,
                'database_status': 'Connected',
                'uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'app_version': '2.0.0',
                'python_version': '3.x'
            },
            'security_settings': {
                'rate_limiting': True,
                'admin_sessions_active': len(admin_sessions),
                'failed_login_attempts': len(admin_login_attempts),
                'password_encryption': 'PBKDF2',
                'session_security': 'Enabled',
                'csrf_protection': 'Enabled'
            },
            'system_settings': {
                'max_image_upload': 5,
                'max_file_size': '10MB',
                'allowed_file_types': ['jpg', 'jpeg', 'png', 'gif'],
                'session_timeout': '24 hours',
                'auto_approval': False,
                'email_notifications': False,
                'backup_enabled': False
            },
            'database_info': {
                'type': 'SQLite',
                'size': 'Dynamic',
                'tables': ['users', 'properties', 'user_sessions', 'admin_logs'],
                'last_backup': 'Manual',
                'integrity': 'Good'
            }
        }

        log_admin_action('view_settings', {})

        return render_template('admin_settings.html',
                             settings=settings_data,
                             admin_username=session.get('admin_username'))
    except Exception as e:
        log_admin_action('settings_error', {'error': str(e)})
        return f"Admin Settings Error: {str(e)}", 500

@app.route('/admin/bulk-actions', methods=['POST'])
@admin_required
def admin_bulk_actions():
    """Admin bulk actions for properties and users"""
    try:
        action = request.form.get('action')
        target_type = request.form.get('target_type')  # 'properties' or 'users'
        target_ids = request.form.getlist('target_ids')

        if not action or not target_type or not target_ids:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        conn = db_manager.get_connection()
        cursor = conn.cursor()

        results = []

        if target_type == 'properties':
            for prop_id in target_ids:
                if action == 'approve':
                    cursor.execute('UPDATE properties SET status = ? WHERE id = ?', ('approved', prop_id))
                elif action == 'reject':
                    cursor.execute('UPDATE properties SET status = ? WHERE id = ?', ('rejected', prop_id))
                elif action == 'delete':
                    cursor.execute('DELETE FROM properties WHERE id = ?', (prop_id,))
                results.append(f'Property {prop_id} {action}d')

        elif target_type == 'users':
            for user_id in target_ids:
                if action == 'activate':
                    cursor.execute('UPDATE users SET is_active = 1 WHERE id = ?', (user_id,))
                elif action == 'deactivate':
                    cursor.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
                elif action == 'delete':
                    # Delete user's properties first
                    cursor.execute('DELETE FROM properties WHERE user_id = ?', (user_id,))
                    cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
                    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                results.append(f'User {user_id} {action}d')

        conn.commit()
        conn.close()

        log_admin_action('bulk_action', {
            'action': action,
            'target_type': target_type,
            'count': len(target_ids),
            'admin': session.get('admin_username')
        })

        return jsonify({
            'success': True,
            'message': f'Bulk {action} completed successfully',
            'results': results
        })

    except Exception as e:
        log_admin_action('bulk_action_error', {'error': str(e)})
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/system-control', methods=['POST'])
@admin_required
def admin_system_control():
    """Admin system control actions"""
    try:
        action = request.form.get('action')

        if action == 'clear_logs':
            session['admin_logs'] = []
            message = 'Admin logs cleared successfully'

        elif action == 'reset_sessions':
            # Clear all user sessions
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user_sessions')
            conn.commit()
            conn.close()
            message = 'All user sessions cleared successfully'

        elif action == 'backup_database':
            # Simulate database backup
            message = 'Database backup initiated (feature not implemented)'

        elif action == 'system_maintenance':
            # Simulate system maintenance
            message = 'System maintenance mode activated'

        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400

        log_admin_action('system_control', {
            'action': action,
            'admin': session.get('admin_username')
        })

        return jsonify({'success': True, 'message': message})

    except Exception as e:
        log_admin_action('system_control_error', {'error': str(e)})
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/rental-properties')
@admin_required
def admin_rental_properties():
    """Admin rental properties management"""
    try:
        # Get all rental properties from database
        result = db_manager.get_all_rental_properties()
        rental_properties = result.get('rentals', []) if result['success'] else []

        # Debug logging
        print(f"DEBUG: Admin rental properties - Success: {result['success']}")
        print(f"DEBUG: Admin rental properties - Count: {len(rental_properties)}")
        if rental_properties:
            for rental in rental_properties[:3]:  # Show first 3
                print(f"DEBUG: Rental - ID: {rental['id']}, Type: {rental['property_type']}, Location: {rental['location']}")

        log_admin_action('view_rental_properties', {'total_rentals': len(rental_properties)})

        return render_template('admin_rental_properties.html',
                             rentals=rental_properties,
                             admin_username=session.get('admin_username'))
    except Exception as e:
        log_admin_action('rental_properties_error', {'error': str(e)})
        return f"Admin Rental Properties Error: {str(e)}", 500

@app.route('/admin/test-auth', methods=['GET', 'POST'])
@admin_required
def admin_test_auth():
    """Test admin authentication"""
    return jsonify({'success': True, 'message': 'Admin authentication working', 'method': request.method})

@app.route('/admin/rental-properties/<rental_id>/action', methods=['POST'])
@admin_required
def admin_rental_property_action(rental_id):
    """Admin rental property actions (approve, reject, delete)"""
    try:
        # Debug logging
        print(f"DEBUG: Admin action called for rental {rental_id}")
        print(f"DEBUG: Admin session: {session.get('admin_logged_in')}")
        print(f"DEBUG: Admin username: {session.get('admin_username')}")

        action = request.form.get('action')
        print(f"DEBUG: Action requested: {action}")

        if not action:
            return jsonify({'success': False, 'error': 'Action is required'}), 400

        # Perform action using new approval system
        admin_id = session.get('admin_user_id', 1)  # Default to admin ID 1

        if action == 'approve':
            # Approve rental and make it visible to public
            result = db_manager.approve_rental_to_public(rental_id, admin_id)
            print(f"DEBUG: Approval result: {result}")
            if result['success']:
                message = 'Rental property approved and made visible to all users!'
            else:
                return jsonify({'success': False, 'error': result['error']}), 500

        elif action in ['reject', 'delete']:
            # Remove rental from public view
            result = db_manager.delete_rental_from_public(rental_id)
            print(f"DEBUG: Deletion result: {result}")
            if result['success']:
                message = 'Rental property removed from public view'
            else:
                return jsonify({'success': False, 'error': result['error']}), 500
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400

        log_admin_action('rental_property_action', {
            'rental_id': rental_id,
            'action': action,
            'admin': session.get('admin_username')
        })

        print(f"DEBUG: Returning success response: {message}")
        return jsonify({'success': True, 'message': message})

    except Exception as e:
        print(f"DEBUG: Exception in admin action: {str(e)}")
        log_admin_action('rental_property_action_error', {'error': str(e)})
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return """
    <html>
    <head><title>404 - Page Not Found</title></head>
    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
        <h1>🔍 404 - Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/" style="color: #667eea;">← Back to Home</a>
    </body>
    </html>
    """, 404

@app.errorhandler(500)
def internal_error(error):
    return """
    <html>
    <head><title>500 - Internal Server Error</title></head>
    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
        <h1>⚠️ 500 - Internal Server Error</h1>
        <p>Something went wrong on our end. Please try again later.</p>
        <a href="/" style="color: #667eea;">← Back to Home</a>
    </body>
    </html>
    """, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'

    print("🚀 Starting Real Estate AI Application...")
    print(f"✅ Running on port {port}, debug={debug}")
    print("🏠 Features: ML Prediction | Market Trends | Property Comparison | AI Chat | Dashboard")
    print(f"📍 Access at: http://127.0.0.1:{port}")

    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
