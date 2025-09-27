"""
Advanced Analytics and Reporting Module
"""

import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, Counter

class AnalyticsManager:
    """Advanced analytics for real estate platform"""
    
    def __init__(self):
        self.user_sessions = defaultdict(list)
        self.property_views = defaultdict(int)
        self.search_queries = []
        self.prediction_history = []
        self.rental_bookings = []
        
    def track_user_activity(self, session_id, activity_type, data=None):
        """Track user activity for analytics"""
        activity = {
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'data': data or {}
        }
        self.user_sessions[session_id].append(activity)
    
    def track_property_view(self, property_id, location, property_type):
        """Track property views for popularity analysis"""
        self.property_views[f"{location}_{property_type}"] += 1
        
    def track_search_query(self, query, results_count, user_session):
        """Track search queries for trend analysis"""
        search_data = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'results_count': results_count,
            'session_id': user_session
        }
        self.search_queries.append(search_data)
    
    def track_prediction(self, input_data, predicted_price, confidence):
        """Track price predictions for model performance"""
        prediction_data = {
            'timestamp': datetime.now().isoformat(),
            'input': input_data,
            'predicted_price': predicted_price,
            'confidence': confidence
        }
        self.prediction_history.append(prediction_data)
    
    def get_popular_locations(self, limit=10):
        """Get most popular locations based on views"""
        location_counts = Counter()
        for key, count in self.property_views.items():
            location = key.split('_')[0]
            location_counts[location] += count
        
        return location_counts.most_common(limit)
    
    def get_search_trends(self, days=7):
        """Get search trends for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_searches = [
            s for s in self.search_queries 
            if datetime.fromisoformat(s['timestamp']) > cutoff_date
        ]
        
        # Analyze search patterns
        query_words = []
        for search in recent_searches:
            query_words.extend(search['query'].lower().split())
        
        return Counter(query_words).most_common(20)
    
    def get_price_prediction_stats(self):
        """Get statistics about price predictions"""
        if not self.prediction_history:
            return {}
        
        prices = [p['predicted_price'] for p in self.prediction_history]
        
        return {
            'total_predictions': len(self.prediction_history),
            'avg_predicted_price': np.mean(prices),
            'median_predicted_price': np.median(prices),
            'min_predicted_price': np.min(prices),
            'max_predicted_price': np.max(prices),
            'price_std': np.std(prices)
        }
    
    def get_user_engagement_metrics(self):
        """Get user engagement statistics"""
        if not self.user_sessions:
            return {}
        
        session_lengths = []
        page_views_per_session = []
        
        for session_id, activities in self.user_sessions.items():
            if len(activities) > 1:
                start_time = datetime.fromisoformat(activities[0]['timestamp'])
                end_time = datetime.fromisoformat(activities[-1]['timestamp'])
                session_length = (end_time - start_time).total_seconds() / 60  # minutes
                session_lengths.append(session_length)
            
            page_views_per_session.append(len(activities))
        
        return {
            'total_sessions': len(self.user_sessions),
            'avg_session_length': np.mean(session_lengths) if session_lengths else 0,
            'avg_page_views_per_session': np.mean(page_views_per_session),
            'bounce_rate': len([s for s in page_views_per_session if s == 1]) / len(page_views_per_session) * 100
        }
    
    def generate_market_insights(self, location_data):
        """Generate AI-powered market insights"""
        insights = []
        
        # Popular locations insight
        popular_locations = self.get_popular_locations(5)
        if popular_locations:
            top_location = popular_locations[0][0]
            insights.append({
                'type': 'popularity',
                'title': f'{top_location} is trending',
                'description': f'{top_location} has the highest user interest with {popular_locations[0][1]} property views.',
                'icon': 'fas fa-fire',
                'color': 'danger'
            })
        
        # Price prediction insights
        price_stats = self.get_price_prediction_stats()
        if price_stats:
            avg_price = price_stats['avg_predicted_price']
            insights.append({
                'type': 'pricing',
                'title': f'Average predicted price: ₹{avg_price:.1f}L',
                'description': f'Based on {price_stats["total_predictions"]} recent predictions.',
                'icon': 'fas fa-chart-line',
                'color': 'success'
            })
        
        # Search trends insight
        search_trends = self.get_search_trends()
        if search_trends:
            top_search_term = search_trends[0][0]
            insights.append({
                'type': 'search',
                'title': f'"{top_search_term}" is a popular search term',
                'description': f'Users are actively searching for properties related to {top_search_term}.',
                'icon': 'fas fa-search',
                'color': 'info'
            })
        
        return insights
    
    def export_analytics_data(self):
        """Export analytics data for external analysis"""
        return {
            'user_sessions': dict(self.user_sessions),
            'property_views': dict(self.property_views),
            'search_queries': self.search_queries,
            'prediction_history': self.prediction_history,
            'rental_bookings': self.rental_bookings,
            'generated_at': datetime.now().isoformat()
        }
    
    def get_conversion_funnel(self):
        """Analyze user conversion funnel"""
        funnel_data = {
            'visitors': len(self.user_sessions),
            'property_viewers': 0,
            'prediction_users': len(self.prediction_history),
            'contact_inquiries': 0,
            'rental_bookings': len(self.rental_bookings)
        }
        
        # Count users who viewed properties
        for session_activities in self.user_sessions.values():
            if any(activity['type'] == 'property_view' for activity in session_activities):
                funnel_data['property_viewers'] += 1
            if any(activity['type'] == 'contact_inquiry' for activity in session_activities):
                funnel_data['contact_inquiries'] += 1
        
        return funnel_data
    
    def get_real_time_stats(self):
        """Get real-time platform statistics"""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)
        
        # Recent activity counts
        recent_predictions = len([
            p for p in self.prediction_history 
            if datetime.fromisoformat(p['timestamp']) > last_hour
        ])
        
        recent_searches = len([
            s for s in self.search_queries 
            if datetime.fromisoformat(s['timestamp']) > last_hour
        ])
        
        daily_predictions = len([
            p for p in self.prediction_history 
            if datetime.fromisoformat(p['timestamp']) > last_24h
        ])
        
        return {
            'predictions_last_hour': recent_predictions,
            'searches_last_hour': recent_searches,
            'predictions_last_24h': daily_predictions,
            'total_property_views': sum(self.property_views.values()),
            'active_sessions': len(self.user_sessions)
        }

# Global analytics manager instance
analytics_manager = AnalyticsManager()

def track_page_view(page_name, session_id, additional_data=None):
    """Helper function to track page views"""
    analytics_manager.track_user_activity(
        session_id, 
        'page_view', 
        {'page': page_name, **(additional_data or {})}
    )

def track_feature_usage(feature_name, session_id, success=True, additional_data=None):
    """Helper function to track feature usage"""
    analytics_manager.track_user_activity(
        session_id,
        'feature_usage',
        {
            'feature': feature_name,
            'success': success,
            **(additional_data or {})
        }
    )

def get_dashboard_analytics():
    """Get analytics data for admin dashboard"""
    return {
        'popular_locations': analytics_manager.get_popular_locations(),
        'search_trends': analytics_manager.get_search_trends(),
        'price_stats': analytics_manager.get_price_prediction_stats(),
        'engagement_metrics': analytics_manager.get_user_engagement_metrics(),
        'conversion_funnel': analytics_manager.get_conversion_funnel(),
        'real_time_stats': analytics_manager.get_real_time_stats(),
        'market_insights': analytics_manager.generate_market_insights({})
    }
