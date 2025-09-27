"""
Security utilities for Real Estate AI application
"""

import re
import html
import hashlib
import secrets
import time
from functools import wraps
from flask import request, session, jsonify, abort

class SecurityManager:
    """Centralized security management"""
    
    def __init__(self):
        self.rate_limits = {}
        self.blocked_ips = set()
        self.session_tokens = {}
        
    def sanitize_input(self, data):
        """Sanitize user input to prevent XSS and injection attacks"""
        if isinstance(data, str):
            # HTML escape to prevent XSS
            data = html.escape(data)

            # Remove potentially dangerous HTML tags and scripts
            dangerous_patterns = [
                r'<script[^>]*>.*?</script>',
                r'<iframe[^>]*>.*?</iframe>',
                r'<object[^>]*>.*?</object>',
                r'<embed[^>]*>.*?</embed>',
                r'<link[^>]*>',
                r'<meta[^>]*>',
                r'javascript:',
                r'vbscript:',
                r'data:text/html',
                r'on\w+\s*=',  # Event handlers like onclick, onload, etc.
            ]

            for pattern in dangerous_patterns:
                data = re.sub(pattern, '', data, flags=re.IGNORECASE | re.DOTALL)

            # Remove SQL injection patterns
            sql_patterns = [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
                r"(--|#|/\*|\*/)",
                r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
                r"(\bOR\s+\d+\s*=\s*\d+)",
                r"(\'\s*(OR|AND)\s*\')",
            ]
            for pattern in sql_patterns:
                data = re.sub(pattern, "", data, flags=re.IGNORECASE)

            return data.strip()

        elif isinstance(data, dict):
            return {key: self.sanitize_input(value) for key, value in data.items()}

        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]

        return data
    
    def validate_phone_number(self, phone):
        """Validate phone number format"""
        if not phone:
            return False
        
        # Remove all non-digit characters
        phone_digits = re.sub(r'\D', '', phone)
        
        # Check if it's a valid Indian mobile number
        if len(phone_digits) == 10 and phone_digits.startswith(('6', '7', '8', '9')):
            return True
        elif len(phone_digits) == 12 and phone_digits.startswith('91'):
            return True
        
        return False
    
    def validate_email(self, email):
        """Validate email format"""
        if not email:
            return True  # Email is optional
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    def validate_property_data(self, data):
        """Validate property data"""
        errors = []
        
        # Required fields
        required_fields = ['location', 'size', 'total_sqft']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"{field} is required")
        
        # Numeric validations
        try:
            sqft = float(data.get('total_sqft', 0))
            if sqft < 100 or sqft > 50000:
                errors.append("Total sqft must be between 100 and 50,000")
        except (ValueError, TypeError):
            errors.append("Total sqft must be a valid number")
        
        # Phone number validation
        if 'contact_number' in data:
            if not self.validate_phone_number(data['contact_number']):
                errors.append("Invalid phone number format")
        
        # Email validation
        if 'email' in data:
            if not self.validate_email(data['email']):
                errors.append("Invalid email format")
        
        return errors
    
    def check_rate_limit(self, identifier, max_requests=10, window_seconds=60):
        """Check if request is within rate limits"""
        current_time = time.time()
        
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []
        
        # Remove old requests outside the window
        self.rate_limits[identifier] = [
            req_time for req_time in self.rate_limits[identifier]
            if current_time - req_time < window_seconds
        ]
        
        # Check if limit exceeded
        if len(self.rate_limits[identifier]) >= max_requests:
            return False
        
        # Add current request
        self.rate_limits[identifier].append(current_time)
        return True
    
    def generate_csrf_token(self):
        """Generate CSRF token"""
        token = secrets.token_urlsafe(32)
        session['csrf_token'] = token
        return token
    
    def validate_csrf_token(self, token):
        """Validate CSRF token"""
        return token and session.get('csrf_token') == token
    
    def hash_sensitive_data(self, data):
        """Hash sensitive data for storage"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def is_safe_redirect_url(self, url):
        """Check if redirect URL is safe"""
        if not url:
            return False
        
        # Only allow relative URLs or same domain
        if url.startswith('/'):
            return True
        
        # Block external redirects
        dangerous_patterns = [
            r'https?://',
            r'ftp://',
            r'javascript:',
            r'data:',
            r'vbscript:'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True

# Global security manager instance
security_manager = SecurityManager()

def rate_limit(max_requests=10, window_seconds=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use IP address as identifier
            identifier = request.environ.get('REMOTE_ADDR', 'unknown')
            
            if not security_manager.check_rate_limit(identifier, max_requests, window_seconds):
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again later.'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_request_data():
    """Sanitize incoming request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Note: We can't modify request.json or request.form directly
                # Instead, we'll sanitize data within the route functions
                return f(*args, **kwargs)
            except Exception as e:
                print(f"Error in sanitize_request_data: {e}")
                return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_property_input():
    """Validate property input data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() if request.is_json else request.form.to_dict()
            
            errors = security_manager.validate_property_data(data)
            if errors:
                return jsonify({
                    'success': False,
                    'error': 'Validation failed',
                    'details': errors
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_csrf_token():
    """Require CSRF token for POST requests"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
                if not security_manager.validate_csrf_token(token):
                    return jsonify({
                        'success': False,
                        'error': 'Invalid CSRF token'
                    }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_security_event(event_type, details):
    """Log security events"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    ip_address = request.environ.get('REMOTE_ADDR', 'unknown')
    user_agent = request.headers.get('User-Agent', 'unknown')
    
    log_entry = {
        'timestamp': timestamp,
        'event_type': event_type,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'details': details
    }
    
    # In production, this should write to a proper logging system
    print(f"SECURITY EVENT: {log_entry}")

def get_client_ip():
    """Get client IP address safely"""
    # Check for forwarded IP (behind proxy)
    forwarded_ip = request.headers.get('X-Forwarded-For')
    if forwarded_ip:
        return forwarded_ip.split(',')[0].strip()
    
    # Check for real IP (behind proxy)
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Default to remote address
    return request.environ.get('REMOTE_ADDR', 'unknown')

def is_suspicious_request():
    """Detect suspicious request patterns"""
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Check for common bot patterns
    bot_patterns = [
        'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
        'python-requests', 'postman', 'insomnia'
    ]
    
    for pattern in bot_patterns:
        if pattern in user_agent:
            return True
    
    # Check for missing user agent
    if not user_agent or len(user_agent) < 10:
        return True
    
    return False
