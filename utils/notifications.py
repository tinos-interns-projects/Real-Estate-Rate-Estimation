"""
Advanced Notification System
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from collections import defaultdict
import requests

class NotificationManager:
    """Manage notifications for users and property owners"""
    
    def __init__(self):
        self.notifications = defaultdict(list)
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': '',  # Configure with actual email
            'password': '',  # Configure with actual password
            'enabled': False  # Set to True when configured
        }
        self.sms_config = {
            'api_key': '',  # Configure with SMS service API key
            'enabled': False
        }
    
    def add_notification(self, user_id, notification_type, title, message, data=None):
        """Add a notification for a user"""
        notification = {
            'id': f"notif_{len(self.notifications[user_id]) + 1}",
            'type': notification_type,
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': datetime.now().isoformat(),
            'read': False,
            'priority': 'normal'
        }
        
        self.notifications[user_id].append(notification)
        return notification['id']
    
    def mark_as_read(self, user_id, notification_id):
        """Mark a notification as read"""
        for notification in self.notifications[user_id]:
            if notification['id'] == notification_id:
                notification['read'] = True
                return True
        return False
    
    def get_user_notifications(self, user_id, unread_only=False):
        """Get notifications for a user"""
        user_notifications = self.notifications[user_id]
        
        if unread_only:
            return [n for n in user_notifications if not n['read']]
        
        return user_notifications
    
    def send_property_inquiry_notification(self, owner_contact, property_title, buyer_name, buyer_contact, message):
        """Send notification to property owner about inquiry"""
        notification_title = f"New inquiry for {property_title}"
        notification_message = f"""
        You have received a new inquiry for your property "{property_title}".
        
        Buyer Details:
        Name: {buyer_name}
        Contact: {buyer_contact}
        
        Message: {message}
        
        Please contact the buyer directly to discuss further.
        """
        
        # Add to owner's notifications (using contact as user_id)
        self.add_notification(
            owner_contact,
            'property_inquiry',
            notification_title,
            notification_message,
            {
                'property_title': property_title,
                'buyer_name': buyer_name,
                'buyer_contact': buyer_contact,
                'inquiry_message': message
            }
        )
        
        # Send SMS if configured
        if self.sms_config['enabled']:
            self.send_sms(
                owner_contact,
                f"New property inquiry for {property_title} from {buyer_name}. Contact: {buyer_contact}"
            )
        
        return True
    
    def send_rental_booking_notification(self, owner_contact, property_title, guest_name, guest_contact, check_in, check_out):
        """Send notification to rental property owner about booking"""
        notification_title = f"New booking for {property_title}"
        notification_message = f"""
        You have received a new booking request for your rental property "{property_title}".
        
        Guest Details:
        Name: {guest_name}
        Contact: {guest_contact}
        Check-in: {check_in}
        Check-out: {check_out}
        
        Please contact the guest to confirm the booking.
        """
        
        self.add_notification(
            owner_contact,
            'rental_booking',
            notification_title,
            notification_message,
            {
                'property_title': property_title,
                'guest_name': guest_name,
                'guest_contact': guest_contact,
                'check_in': check_in,
                'check_out': check_out
            }
        )
        
        # Send SMS if configured
        if self.sms_config['enabled']:
            self.send_sms(
                owner_contact,
                f"New rental booking for {property_title} from {guest_name}. Dates: {check_in} to {check_out}"
            )
        
        return True
    
    def send_price_alert(self, user_id, location, current_price, threshold_price, alert_type):
        """Send price alert notification"""
        if alert_type == 'above':
            title = f"Price Alert: {location} prices above ₹{threshold_price}L"
            message = f"Properties in {location} are now priced above your alert threshold of ₹{threshold_price}L. Current average: ₹{current_price}L"
        else:
            title = f"Price Alert: {location} prices below ₹{threshold_price}L"
            message = f"Properties in {location} are now priced below your alert threshold of ₹{threshold_price}L. Current average: ₹{current_price}L"
        
        self.add_notification(
            user_id,
            'price_alert',
            title,
            message,
            {
                'location': location,
                'current_price': current_price,
                'threshold_price': threshold_price,
                'alert_type': alert_type
            }
        )
    
    def send_market_update(self, user_id, location, trend_data):
        """Send market trend update"""
        trend_direction = "rising" if trend_data['growth_rate'] > 0 else "falling"
        title = f"Market Update: {location} prices {trend_direction}"
        message = f"""
        Market update for {location}:
        
        Current trend: {trend_direction.title()} by {abs(trend_data['growth_rate']):.1f}%
        Average price: ₹{trend_data['avg_price']:.1f} Lakhs
        Investment rating: {trend_data['investment_rating']}
        
        This could be a good time to {"sell" if trend_direction == "rising" else "buy"} in this area.
        """
        
        self.add_notification(
            user_id,
            'market_update',
            title,
            message,
            trend_data
        )
    
    def send_email(self, to_email, subject, body, html_body=None):
        """Send email notification"""
        if not self.email_config['enabled']:
            print(f"Email not configured. Would send: {subject} to {to_email}")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_config['username']
            msg['To'] = to_email
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def send_sms(self, phone_number, message):
        """Send SMS notification"""
        if not self.sms_config['enabled']:
            print(f"SMS not configured. Would send to {phone_number}: {message}")
            return False
        
        # This is a placeholder for SMS integration
        # You would integrate with services like Twilio, AWS SNS, etc.
        try:
            # Example Twilio integration (requires twilio library)
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # message = client.messages.create(
            #     body=message,
            #     from_='+1234567890',
            #     to=phone_number
            # )
            print(f"SMS sent to {phone_number}: {message}")
            return True
        except Exception as e:
            print(f"Failed to send SMS: {e}")
            return False
    
    def send_push_notification(self, user_id, title, body, data=None):
        """Send push notification (placeholder for web push)"""
        # This would integrate with web push services
        notification_data = {
            'title': title,
            'body': body,
            'data': data or {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to user's notifications
        self.add_notification(user_id, 'push', title, body, data)
        
        print(f"Push notification sent to {user_id}: {title}")
        return True
    
    def create_notification_preferences(self, user_id):
        """Create default notification preferences for a user"""
        preferences = {
            'email_notifications': True,
            'sms_notifications': True,
            'push_notifications': True,
            'price_alerts': True,
            'market_updates': True,
            'property_inquiries': True,
            'rental_bookings': True,
            'frequency': 'immediate'  # immediate, daily, weekly
        }
        
        return preferences
    
    def get_notification_stats(self):
        """Get notification statistics"""
        total_notifications = sum(len(notifications) for notifications in self.notifications.values())
        unread_count = sum(
            len([n for n in notifications if not n['read']]) 
            for notifications in self.notifications.values()
        )
        
        notification_types = defaultdict(int)
        for notifications in self.notifications.values():
            for notification in notifications:
                notification_types[notification['type']] += 1
        
        return {
            'total_notifications': total_notifications,
            'unread_count': unread_count,
            'notification_types': dict(notification_types),
            'active_users': len(self.notifications)
        }
    
    def cleanup_old_notifications(self, days=30):
        """Clean up notifications older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for user_id in self.notifications:
            self.notifications[user_id] = [
                notification for notification in self.notifications[user_id]
                if datetime.fromisoformat(notification['timestamp']) > cutoff_date
            ]

# Global notification manager instance
notification_manager = NotificationManager()

def send_property_inquiry(owner_contact, property_title, buyer_name, buyer_contact, message):
    """Helper function to send property inquiry notification"""
    return notification_manager.send_property_inquiry_notification(
        owner_contact, property_title, buyer_name, buyer_contact, message
    )

def send_rental_booking(owner_contact, property_title, guest_name, guest_contact, check_in, check_out):
    """Helper function to send rental booking notification"""
    return notification_manager.send_rental_booking_notification(
        owner_contact, property_title, guest_name, guest_contact, check_in, check_out
    )

def get_user_notifications(user_id, unread_only=False):
    """Helper function to get user notifications"""
    return notification_manager.get_user_notifications(user_id, unread_only)

def mark_notification_read(user_id, notification_id):
    """Helper function to mark notification as read"""
    return notification_manager.mark_as_read(user_id, notification_id)
